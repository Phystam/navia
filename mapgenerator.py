import json
import os
import random
import numpy as np
from PIL import Image
from noise import snoise2
from collections import deque
from scipy.ndimage import distance_transform_edt, binary_opening, binary_closing, label, gaussian_filter, binary_erosion, binary_dilation
from datetime import datetime
import cv2
from scipy.spatial import Delaunay
import sys
import io
from skimage.graph import route_through_array
from skimage.morphology import label as sk_label

# Force stdout to use UTF-8 encoding for Windows environments
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class MapGenerator:
    """
    Generates a fictional, Japanese-style map for Simutrans.
    Reads parameters from a config file to generate terrain and outputs it as a PNG image.
    """

    def __init__(self, config_path):
        print("Step 1: Loading settings and initializing")
        self.config = self._load_config(config_path)
        self.timestamp = datetime.now().strftime('%y_%m_%d_%H_%M_%S')
        self._initialize()

    def _load_config(self, config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _initialize(self):
        self.width = self.config['map_width']
        self.height = self.config['map_height']
        self.seed = self.config['random_seed']
        random.seed(self.seed)
        np.random.seed(self.seed)
        self.height_map = np.zeros((self.height, self.width), dtype=np.int16)
        self.grayscale_map = np.zeros((self.height, self.width), dtype=np.uint8)
        self.noise_scale = 250.0
        self.octaves = 6
        self.persistence = 0.5
        self.lacunarity = 2.0
        self.unconnected_edges = set()
        self.rivers = []
        print(f"  - Map size: {self.width}x{self.height}")
        print(f"  - Random seed: {self.seed}")
        print(f"  - Timestamp: {self.timestamp}")


    def generate_map(self, output_dir):
        # 1-5. 土地の基本形状と海岸線を生成
        self._generate_base_noise()
        self._apply_ocean_buffer_influence()
        self._form_landmass()
        self._process_coastline()
        self._save_debug_mask(output_dir)

        # --- V83/V84: Erosion Resistance Model ---
        # 6. 侵食耐性マップを生成
        resistance_map = self._create_erosion_resistance_map_v83()
        
        # 7. ベースとなる地形を形成
        self._shape_base_topography_v84(resistance_map)

        # 8. 水力侵食モデルで川を生成
        river_mask = self._hydraulic_erosion_rivers_v80(resistance_map)
        self._final_river_mask = river_mask

        # 9. 地形復元と最終ディテール
        self._apply_mounding_and_details_v81(resistance_map)
        
        # 10. ★★★ V85仕様の最終化 ★★★
        self._finalize_map_v85_style()
        
        return self.grayscale_map

    def _shape_base_topography_v84(self, resistance_map):
        """V84: Shapes base topography with ridge protection during smoothing."""
        print("Step 7 (V84): Shaping blended base topography with ridge protection...")
        self.height_map.fill(0)
        if resistance_map is None: return

        # Model A: 平野のベース地形
        plains_base = (5 + self.base_noise * 10).astype(np.int16)
        
        # Model B: 山岳のベース地形
        mountain_base = np.zeros_like(self.height_map, dtype=np.int16)
        ridge_mask = np.zeros_like(self.land_mask, dtype=bool) # 保護マスク用に初期化
        mountain_zone = resistance_map > 0.4
        if np.any(mountain_zone):
            peaks, net = self._create_ridge_network(mountain_zone)
            if peaks:
                ridge_h, ridge_m = self._assign_ridge_heights_v54(peaks, net)
                ridge_mask = ridge_m # 保護マスクとして稜線マスクを取得
                dist_r, indices = distance_transform_edt(~ridge_mask, return_indices=True)
                propagated_ridge_h = ridge_h[indices[0], indices[1]]
                mountain_base = self._shape_slopes_by_warping_v66(propagated_ridge_h, self.land_mask, ridge_mask)
        
        # 侵食耐性に基づいて2つのモデルを合成
        blended_map = plains_base * (1 - resistance_map) + mountain_base * resistance_map
        
        # ★★★★★ V84: 稜線保護を伴う段階的平滑化 ★★★★★
        print("  - Applying smoothing with ridge protection...")
        # 1. まず全体に弱い平滑化をかける
        weakly_smoothed_map = gaussian_filter(blended_map, sigma=0.05)

        # 2. 強い平滑化をかけたマップを別途用意
        strongly_smoothed_map = gaussian_filter(blended_map, sigma=3.0)
        
        # 3. 稜線とその周辺を保護するマスクを作成
        protected_mask = binary_dilation(ridge_mask, iterations=12)

        # 4. 保護マスクの外側だけ、強い平滑化を適用
        final_blended_map = weakly_smoothed_map
        final_blended_map[~protected_mask] = strongly_smoothed_map[~protected_mask]
        # ★★★★★ END OF V84 Smoothing ★★★★★

        max_h = 45 + self.config['mountain_level'] * 15
        self.height_map = np.clip(final_blended_map, 0, max_h).astype(np.int16)
        self.height_map[~self.land_mask] = 0

    def _create_erosion_resistance_map_v83(self):
        """V83: Creates an erosion resistance map (0.0 to 1.0).
        High resistance = mountains, Low resistance = plains.
        """
        print("Step 6 (V83): Creating erosion resistance map...")
        if not np.any(self.land_mask): return None

        dist_from_sea = distance_transform_edt(self.land_mask)
        dist_norm = (dist_from_sea / np.max(dist_from_sea)) if np.max(dist_from_sea) > 0 else 0
        
        # 山が海岸にせり出す効果
        mountain_lv = self.config['mountain_level']
        coast_mountain_noise = self._create_detail_noise(250, 6, 15001)
        # mountain_levelが高いほど、海岸沿いでも耐性が高くなる確率が上がる
        resistance = dist_norm + (coast_mountain_noise - 0.4) * (mountain_lv / 5.0)
        
        # 0-1の範囲に正規化
        resistance = np.clip(resistance, 0, 1.5) # 範囲外の値をクリップ
        if np.any(self.land_mask):
            land_res = resistance[self.land_mask]
            min_res, max_res = np.min(land_res), np.max(land_res)
            if max_res > min_res:
                 resistance[self.land_mask] = (land_res - min_res) / (max_res - min_res)
        
        # plains_levelで最終調整。高いほど全体の耐性が下がる（平野が増える）
        resistance = resistance ** (1.8 / self.config['plains_level'])
        
        return resistance
        
    def _hydraulic_erosion_rivers_v80(self, resistance_map):
        """V83-MOD: Creates rivers using a hydraulic erosion model."""
        print("Step 8 (V83): Carving rivers with hydraulic erosion model...")
        river_mask = np.zeros_like(self.land_mask, dtype=bool)
        num_rivers = int(self.config['river_density_level'] * (self.width * self.height / (512*512)) * 6)
        if resistance_map is None: return river_mask

        source_zone = resistance_map > 0.5
        
        for _ in range(num_rivers):
            source_candidates = source_zone & (self.height_map > np.mean(self.height_map[source_zone] if np.any(source_zone) else 1)) & ~binary_dilation(river_mask, iterations=5)
            if not np.any(source_candidates): continue
            sources_y, sources_x = np.where(source_candidates)
            start_node = (sources_y[random.randint(0, sources_y.size - 1)], sources_x[random.randint(0, sources_x.size - 1)])

            sinks_y, sinks_x = np.where(binary_dilation(~self.land_mask, iterations=2) & self.land_mask)
            if sinks_y.size == 0: break
            # Find closest sink
            dist_sq = (sinks_y - start_node[0])**2 + (sinks_x - start_node[1])**2
            end_node = (sinks_y[np.argmin(dist_sq)], sinks_x[np.argmin(dist_sq)])

            cost = self.height_map.astype(float)
            try:
                path, _ = route_through_array(cost, start_node, end_node, geometric=True, fully_connected=True)
                if len(path) < 20: continue

                temp_mask = np.zeros_like(river_mask, dtype=np.uint8)
                path_len = len(path)
                for i, (y, x) in enumerate(path):
                    if not (0 <= y < self.height and 0 <= x < self.width and self.land_mask[y,x]): break
                    if river_mask[y,x]: break

                    progress = i / path_len
                    flow = 1 + progress * 5
                    next_idx = min(i + 1, path_len - 1)
                    gradient = max(0, self.height_map[y, x] - self.height_map[path[next_idx][0], path[next_idx][1]])
                    
                    erosion_power = flow * gradient * 0.01
                    self.height_map[y, x] -= erosion_power
                    
                    width = 1 + int(progress * 3)
                    cv2.circle(temp_mask, (x, y), width, 1, -1)

                river_mask |= temp_mask.astype(bool)
            except (ValueError, IndexError): continue
            
        # 侵食によって高さが0未満にならないようにする
        self.height_map = np.maximum(0, self.height_map).astype(np.int16)
        return river_mask

    def _apply_mounding_and_details_v81(self, resistance_map):
        """V83-MOD: Applies adaptive mounding and final details."""
        print("Step 9 (V83): Applying adaptive mounding and details...")
        if resistance_map is None: return

        # Moundingは耐性の高いエリアに適用
        mountain_zone = resistance_map > 0.5
        if np.any(mountain_zone):
            print("  - Mounding mountain areas...")
            mountain_heights = self.height_map[mountain_zone]
            max_h = np.max(mountain_heights) if mountain_heights.size > 0 else 1
            if max_h > 0:
                height_diff_norm = (max_h - mountain_heights) / max_h
                mound_strength = 20.0
                mound_amount = (height_diff_norm**1.5) * mound_strength
                mound_noise = self._create_detail_noise(120, 5, 14002)
                mound_amount *= (0.7 + mound_noise[mountain_zone] * 0.6)
                self.height_map[mountain_zone] += mound_amount.astype(np.int16)
        
        self._apply_local_details_v80()

        self.height_map = gaussian_filter(self.height_map.astype(float), sigma=0.8).astype(np.int16)
        
        print("  - Cleaning up coastline artifacts...")
        # 陸地の高さが0未満にならないようにする
        self.land_mask = self.height_map > 0
        self.height_map[~self.land_mask] = 0
        self.height_map[self.land_mask] = np.maximum(1, self.height_map[self.land_mask])

        # --- ★★★ 海岸平坦化処理 (V86 Hotfix) ★★★ ---
        print("  - V86: Flattening coastal area...")
        # 海岸線から内陸へ5ピクセルの範囲を対象とする
        # 距離変換を使い、海（~self.land_mask）からの距離を計算
        dist_from_sea = distance_transform_edt(self.land_mask)
        
        # 海岸から5ピクセル以内の陸地マスクを作成
        coastal_plain_mask = (dist_from_sea > 0) & (dist_from_sea <= 5)
        
        if np.any(coastal_plain_mask):
            # 対象エリアの現在の高さを取得
            current_heights = self.height_map[coastal_plain_mask]
            
            # 目標の高さ（ゲーム内高度1に相当）を設定
            # 内部的なheight_mapの値としては、最終的な正規化を考慮し、
            # 全体の最大高さの5%程度の低い値に設定する
            target_h = np.max(self.height_map) * 0.05
            
            # 現在の高さが目標より高い場合のみ、目標の高さに置き換える
            # これにより、既になだらかな場所を不自然に持ち上げることを防ぐ
            self.height_map[coastal_plain_mask] = np.minimum(current_heights, target_h).astype(np.int16)
            # 最低でも1は保証する
            self.height_map[coastal_plain_mask] = np.maximum(1, self.height_map[coastal_plain_mask])
            print(f"    - Flattened {np.sum(coastal_plain_mask)} pixels along the coastline.")
        # --- ★★★ END OF V86 Hotfix ★★★ ---
        self._simulate_coastal_deposition_v87()

    def _simulate_coastal_deposition_v87(self):
        """V91-MOD: Simulates paired deposition and river mouth erosion."""
        print("  - V91: Simulating paired deposition and river mouth erosion...")
        
        # 1. 堆積ポテンシャルを決定するノイズ
        potential_noise = self._create_detail_noise(scale=300.0, octaves=5, base_offset=9102)
        
        coastline_mask = binary_dilation(self.land_mask) & ~self.land_mask
        if not np.any(coastline_mask): return
        
        coast_y, coast_x = np.where(coastline_mask)
        
        # 2. 海岸線ピクセルにポテンシャル値を割り当てる
        coast_potentials = []
        for i in range(len(coast_y)):
            coast_potentials.append({
                'pos': (coast_x[i], coast_y[i]),
                'potential': potential_noise[coast_y[i], coast_x[i]]
            })
            
        # 3. ポテンシャルが高い順にソートし、上位からペアで堆積エリアを選択
        coast_potentials.sort(key=lambda p: p['potential'], reverse=True)
        num_pairs = int(len(coast_potentials) * 0.1) # 上位10%をペアにする
        
        deposition_mask_uint8 = np.zeros_like(self.land_mask, dtype=np.uint8)
        erosion_mask_uint8 = np.zeros_like(self.land_mask, dtype=np.uint8)

        for i in range(0, num_pairs, 2):
            if i + 1 >= len(coast_potentials): break
            
            p1 = coast_potentials[i]
            p2 = coast_potentials[i+1]
            
            # --- 堆積エリアの生成 ---
            for p in [p1, p2]:
                base_radius = int(5 + p['potential'] * 15) # 半径 5-20
                num_vertices = random.randint(3, 7)
                vertices = []
                for _ in range(num_vertices):
                    angle, radius = random.uniform(0, 2*np.pi), base_radius * random.uniform(0.5, 1.5)
                    vertices.append((int(p['pos'][0] + np.cos(angle)*radius), int(p['pos'][1] + np.sin(angle)*radius)))
                cv2.fillPoly(deposition_mask_uint8, [np.array(vertices)], 255)

            # --- 河口侵食エリアの生成 ---
            # 2つの堆積エリアの中心を結ぶ線分を河口の中心線とする
            cv2.line(erosion_mask_uint8, p1['pos'], p2['pos'], 255, thickness=15)

        # 4. マスクの最終化と適用
        # 堆積マスクの平滑化
        if np.any(deposition_mask_uint8):
            deposition_mask_f = gaussian_filter(deposition_mask_uint8.astype(float), sigma=7)
            deposition_mask = deposition_mask_f > 100
            # 侵食マスクは堆積マスクの内側でのみ有効とする
            erosion_mask = (erosion_mask_uint8 > 0) & deposition_mask
            
            # 堆積処理
            land_to_flatten = deposition_mask & self.land_mask & ~erosion_mask
            sea_to_fill = deposition_mask & ~self.land_mask & ~erosion_mask
            if np.any(land_to_flatten): self.height_map[land_to_flatten] = 1
            if np.any(sea_to_fill):
                self.land_mask[sea_to_fill] = True
                self.height_map[sea_to_fill] = 1
            
            # 侵食処理
            if np.any(erosion_mask):
                self.land_mask[erosion_mask] = False
                self.height_map[erosion_mask] = 0
                print(f"    - Carved {np.sum(erosion_mask)} pixels for river mouths.")

        self.height_map[~self.land_mask] = 0

    def _generate_tiered_rivers_v80(self, zones):
        """V80: Creates a multi-tiered river system with balanced erosion."""
        print("Step 8 (V80): Generating tiered river system with balanced erosion...")
        
        river_mask = np.zeros_like(self.land_mask, dtype=bool)
        cost_map = self.height_map.astype(float)

        def create_rivers(num, river_type, source_zone, sink_mask):
            print(f"  - Carving {num} {river_type} rivers...")
            for _ in range(num):
                path = self._find_river_path_v80(source_zone, sink_mask, cost_map, river_type, river_mask)
                if path:
                    self._carve_river_v80(path, cost_map, river_mask, river_type)
        
        num_major = int(self.config['river_density_level'] * (self.width * self.height / (512*512)) * 1)
        create_rivers(num_major, 'major', zones['mountains'], binary_dilation(~self.land_mask, iterations=2) & self.land_mask)

        num_medium = int(self.config['river_density_level'] * (self.width * self.height / (512*512)) * 2)
        create_rivers(num_medium, 'medium', zones['mountains'] | zones.get('foothills', np.zeros_like(self.land_mask, dtype=bool)), river_mask | (binary_dilation(~self.land_mask, iterations=2) & self.land_mask))

        num_creeks = int(self.config['river_density_level'] * (self.width * self.height / (512*512)) * 3)
        create_rivers(num_creeks, 'creek', zones['mountains'], river_mask)

        return river_mask

    def _carve_river_v80(self, path, cost_map, river_mask, river_type):
        """V80 Helper: Carves a river path using a balanced erosion model."""
        if river_type == 'major':
            params = {'width_mult': 6.0, 'erosion_mult': 0.025}
        elif river_type == 'medium':
            params = {'width_mult': 3.0, 'erosion_mult': 0.01}
        else: # creek
            params = {'width_mult': 1.0, 'erosion_mult': 0.005}

        temp_mask = np.zeros_like(river_mask, dtype=np.uint8)
        path_len = len(path)
        for i, (y, x) in enumerate(path):
            if not (0 <= y < self.height and 0 <= x < self.width and self.land_mask[y,x]):
                break
            if river_mask[y,x]: break

            progress = i / path_len
            flow = 1 + progress * 5
            
            next_idx = min(i + 1, path_len - 1)
            next_y, next_x = path[next_idx]
            gradient = max(0, self.height_map[y, x] - self.height_map[next_y, next_x])
            
            erosion_power = flow * gradient * params['erosion_mult']
            width = 1 + int(progress * params['width_mult'])
            
            radius = width // 2 + 1
            yy, xx = np.ogrid[-radius:radius+1, -radius:radius+1]
            circle_mask = (xx*xx + yy*yy <= radius*radius)
            
            cy, cx = np.clip(y + yy, 0, self.height-1), np.clip(x + xx, 0, self.width-1)
            
            target_area = self.height_map[cy, cx]
            new_height = target_area - erosion_power
            self.height_map[cy, cx] = new_height.astype(np.int16)
            
            cv2.circle(temp_mask, (x, y), width, 1, -1)

        river_mask |= temp_mask.astype(bool)
    def _apply_local_details_v80(self):
        """V80 Helper: Applies complex, overlapping local details."""
        print("  - Applying complex local details...")
        
        num_hubs = 40
        land_y, land_x = np.where(self.land_mask)
        if land_y.size == 0: return

        try:
            indices = np.random.choice(len(land_y), num_hubs, replace=False)
            hub_coords = list(zip(land_y[indices], land_x[indices]))
        except ValueError: # 陸地がハブの数より少ない場合
            hub_coords = list(zip(land_y, land_x))


        print(f"    - Applying {len(hub_coords)} complex detail hubs...")
        for y_hub, x_hub in hub_coords:
            # 2-3層のディテールを重ねる
            for i in range(random.randint(2,3)):
                size = random.randint(3, 6)
                # ハブの中心から少しずらす
                y_start = y_hub - random.randint(-size, size)
                x_start = x_hub - random.randint(-size, size)
                
                # 配列の範囲外に出ないようにクリップ
                y_start = np.clip(y_start, 0, self.height - size)
                x_start = np.clip(x_start, 0, self.width - size)
                
                height_change = random.randint(-3, 3)
                if height_change == 0: continue
                
                mask_area_uint8 = np.zeros((size, size), dtype=np.uint8)
                if random.random() < 0.5:
                    cv2.circle(mask_area_uint8, (size//2, size//2), size//2, 1, -1)
                else: 
                    mask_area_uint8.fill(1)
                
                mask_area_bool = mask_area_uint8.astype(bool)

                # 変更を適用する領域
                target_slice = (slice(y_start, y_start + size), slice(x_start, x_start + size))
                # マスクされた部分にのみ高さを加算
                self.height_map[target_slice][mask_area_bool] += height_change

    def _define_zones_v78(self):
        """V78: Defines terrain zones, strongly forcing mountains to the coast based on config."""
        # V77のロジックは安定していたので、名称のみ変更して再利用
        print("Step 6 (V78): Defining terrain zones...")
        if not np.any(self.land_mask): return {}

        plains_lv = self.config['plains_level']
        mountain_lv = self.config['mountain_level']
        target_plains_ratio = np.clip(plains_lv / (plains_lv + mountain_lv), 0.15, 0.85)

        dist_from_sea = distance_transform_edt(self.land_mask)
        dist_norm = (dist_from_sea / np.max(dist_from_sea)) if np.max(dist_from_sea) > 0 else 0
        
        mountain_force_noise = self._create_detail_noise(200, 6, 13002)
        forced_mountain_mask = mountain_force_noise < (mountain_lv / 10.0)
        
        potential = dist_norm
        land_potential = potential[self.land_mask]
        plains_threshold = np.quantile(land_potential, target_plains_ratio)
        
        zones = {'plains': (potential <= plains_threshold) & self.land_mask & ~forced_mountain_mask}
        zones['mountains'] = self.land_mask & ~zones['plains']

        print(f"  - Actual Plains/Mountain Ratio: "
              f"{np.sum(zones['plains'])/np.sum(self.land_mask):.2f}/"
              f"{np.sum(zones['mountains'])/np.sum(self.land_mask):.2f}")
        return zones

    def _finalize_map_v85_style(self):
        """V85-Fix: Finalizes the map with a robust height mapping, fixing shallow sea color."""
        print("Step 10 (V85): Finalizing map with robust height mapping...")
        
        # 最終的なland_maskとriver_maskを確定
        self.land_mask = self.height_map > 0
        river_mask = getattr(self, '_final_river_mask', np.zeros_like(self.land_mask, dtype=bool)) & self.land_mask

        # --- 海の処理 (修正箇所) ---
        sea_mask = ~self.land_mask
        
        # base_noise (0.0-1.0) を海の輝度値範囲 (0-67) にマッピングする
        # これにより、ノイズが高いほど浅い海（67に近い値）になる
        sea_grayscale_values = (self.base_noise[sea_mask] * 67.0).astype(np.uint8)
        self.grayscale_map[sea_mask] = sea_grayscale_values
        
        # --- 陸の処理 (変更なし) ---
        if not np.any(self.land_mask):
            print("  - No land to process.")
            return

        land_heights = self.height_map[self.land_mask].astype(float)
        
        # height_mapの最大値をゲーム内高度の最大値(32)にマッピングする
        h_max_in_map = np.max(land_heights) if np.any(land_heights) else 1.0
        if h_max_in_map <= 0: h_max_in_map = 1.0
        
        print(f"  - Max internal height value: {h_max_in_map}")
        
        # 各陸地ピクセルのゲーム内高度(0-32)を計算
        game_h = (land_heights / h_max_in_map) * 32.0
        
        # 新しい仕様に基づいて輝度値を計算: g = 70 + (185/32) * h
        grayscale_values = 70.0 + (185.0 / 32.0) * game_h
        
        self.grayscale_map[self.land_mask] = np.clip(grayscale_values, 70, 255).astype(np.uint8)

        # 川をわずかに暗く（低く）して表現
        if np.any(river_mask):
            self.grayscale_map[river_mask] = np.clip(self.grayscale_map[river_mask] - 2, 70, 255)

        # 海岸線を描画 (見た目のため。ゲーム内高度にはほぼ影響しない)
        eroded_land = binary_erosion(self.land_mask, iterations=1)
        coastline = self.land_mask & ~eroded_land
        self.grayscale_map[coastline] = 69

    def _generate_base_noise(self):
        print("Step 2: Generating base noise")
        self.base_noise = np.zeros((self.height, self.width))
        for y in range(self.height):
            for x in range(self.width):
                self.base_noise[y][x] = snoise2(
                    x / self.noise_scale, y / self.noise_scale,
                    octaves=self.octaves, persistence=self.persistence,
                    lacunarity=self.lacunarity, base=self.seed
                )
        self.base_noise = (self.base_noise - np.min(self.base_noise)) / (np.max(self.base_noise) - np.min(self.base_noise))




    def _create_core_mask(self, core):
        core_mask = np.zeros((self.height, self.width), dtype=bool)
        core_mask[core[1], core[0]] = True
        return core_mask

    def _form_landmass(self):
        """V91-MOD: Forms landmass considering island gravity for plate connection."""
        print("Step 3 & 4: Forming landmass (Skeleton Model)")
        island_skeletons = self._create_island_skeletons()
        
        # ガード節: island_skeletonsが空の場合、処理を中断
        if not island_skeletons:
            print("  - Warning: No island skeletons were generated. Checking for continental plates...")
            # 大陸プレートのポテンシャルだけはあるかもしれないので、それを陸地化する
            if hasattr(self, 'continental_plate_potential') and np.any(self.continental_plate_potential):
                print("  - Forming landmass from continental plate potential only.")
                # ポテンシャルとノイズで簡易的な大陸を形成
                plate_noise = self._create_detail_noise(scale=180, octaves=6, base_offset=9101)
                self.land_mask = (self.continental_plate_potential * plate_noise) > 0.4
            else:
                print("  - No landmass source found. Map will be all sea.")
                self.land_mask = np.zeros((self.height, self.width), dtype=bool)
            return

        # --------------------------------------------------------------------
        # 1. 島々の隆起マップを生成
        # --------------------------------------------------------------------
        target_total_pixels = self.width * self.height * self.config['land_ratio']
        y_coords, x_coords = np.ogrid[0:self.height, 0:self.width]
        island_influence_maps = []
        max_influence_radius = min(self.width, self.height) / (len(island_skeletons) * 0.8 + 1)
        print(f"  - Max influence radius per island: {max_influence_radius:.2f}")

        for skeleton in island_skeletons:
            sub_core_influences = []
            for core_x, core_y in skeleton:
                dist_sq = (x_coords - core_x)**2 + (y_coords - core_y)**2
                core_influence = np.exp(-dist_sq / (2 * (max_influence_radius**2)))
                sub_core_influences.append(self.base_noise * 0.5 + core_influence * 1.5)
            island_influence_maps.append(np.maximum.reduce(sub_core_influences))
        
        # 全ての島の影響を統合したマップ
        combined_map = np.maximum.reduce(island_influence_maps)

        # --------------------------------------------------------------------
        # 2. 海峡・湾の形成（複数島が存在する場合のみ）
        # --------------------------------------------------------------------
        if len(island_skeletons) > 1:
            print("  - Using large-scale terrain noise to carve straits and bays between islands...")
            island_centers = [np.mean(skeleton, axis=0).astype(int) for skeleton in island_skeletons]
            dist_maps = np.array([distance_transform_edt(np.invert(self._create_core_mask(c))) for c in island_centers])
            territory_map = np.argmin(dist_maps, axis=0)
            border_mask = np.zeros_like(territory_map, dtype=bool)
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                shifted = np.roll(territory_map, (dy, dx), axis=(0, 1))
                border_mask |= (territory_map != shifted)
            border_dist = distance_transform_edt(~border_mask)
            strait_variation_noise = self._create_detail_noise(scale=self.width / 2.5, octaves=5, base_offset=201)
            bay_carving_noise = self._create_detail_noise(scale=self.width / 1.5, octaves=4, base_offset=202)
            archipelago_noise = self._create_detail_noise(scale=80, octaves=6, base_offset=101)
            base_strait_width = 80
            width_multiplier = 0.5 + strait_variation_noise
            final_strait_width = base_strait_width * width_multiplier
            depression_factor = np.clip(1.0 - (border_dist / final_strait_width), 0, 1)
            bay_depression = (1.0 - bay_carving_noise)**2 * depression_factor
            combined_map -= depression_factor * 0.7
            combined_map -= bay_depression * 0.6
            combined_map += archipelago_noise * depression_factor * 0.25

        # --------------------------------------------------------------------
        # 3. 大陸プレートの最終化と合成
        # --------------------------------------------------------------------
        self.continental_plate_mask = np.zeros_like(self.base_noise, dtype=bool)
        if hasattr(self, 'continental_plate_potential') and np.any(self.continental_plate_potential):
            print("  - V91: Finalizing continental plate using island gravity model...")
            
            all_cores = np.array([core for skeleton in island_skeletons for core in skeleton])
            # all_coresが空でないことを確認
            if all_cores.size > 0:
                center_of_mass = np.mean(all_cores, axis=0)
                print(f"    - Center of island mass: {center_of_mass}")

                y_coords_g, x_coords_g = np.ogrid[0:self.height, 0:self.width]
                dist_to_com_sq = (x_coords_g - center_of_mass[0])**2 + (y_coords_g - center_of_mass[1])**2
                gravity_map = np.exp(-dist_to_com_sq / (2 * (max(self.width, self.height) * 0.5)**2))
                
                plate_noise = self._create_detail_noise(scale=180, octaves=6, base_offset=9101)
                final_plate_strength = self.continental_plate_potential * (0.4 + gravity_map * 0.6) * plate_noise
                self.continental_plate_mask = final_plate_strength > 0.3
            
            if np.any(self.continental_plate_mask):
                 combined_map = np.maximum(combined_map, self.continental_plate_mask.astype(float) * np.max(combined_map))

        # --------------------------------------------------------------------
        # 4. 最終的な陸地マスクの生成（閾値処理）
        # --------------------------------------------------------------------
        flat_map = combined_map.flatten()
        num_pixels_to_assign = min(int(target_total_pixels), len(flat_map))
        if num_pixels_to_assign > 0:
            threshold = np.sort(flat_map)[-num_pixels_to_assign]
            self.land_mask = combined_map >= threshold
        else:
            self.land_mask = np.zeros((self.height, self.width), dtype=bool)
        
        final_ratio = np.sum(self.land_mask) / (self.width * self.height)
        print(f"  - Land ratio (after generation): {final_ratio:.2f} (Target: {self.config['land_ratio']})")

    def _apply_ocean_buffer_influence(self):
        """V91-MOD: Generates a potential area for continental plates."""
        print("... V91: Applying ocean buffer and initializing continental plate potential")
        num_connections = self.config.get('edge_connections', 0)
        
        # --- ★★★ V91修正: プレート「ポテンシャル」マップの生成 ★★★ ---
        self.continental_plate_potential = np.zeros_like(self.base_noise, dtype=float)
        
        if num_connections > 0:
            print(f"  - Generating {num_connections} continental connection potential(s)...")
            all_edges = {'top', 'bottom', 'left', 'right'}
            self.connected_edges = set(random.sample(list(all_edges), k=num_connections))
            print(f"  - Connected edges: {self.connected_edges}")

            # 接続辺に近いほどポテンシャル（接続しやすさ）が高くなるグラデーションを生成
            coords_y, coords_x = np.ogrid[0:self.height, 0:self.width]
            if 'top' in self.connected_edges:
                self.continental_plate_potential = np.maximum(self.continental_plate_potential, 1.0 - (coords_y / (self.height * 0.3)))
            if 'bottom' in self.connected_edges:
                self.continental_plate_potential = np.maximum(self.continental_plate_potential, 1.0 - ((self.height - 1 - coords_y) / (self.height * 0.3)))
            if 'left' in self.connected_edges:
                self.continental_plate_potential = np.maximum(self.continental_plate_potential, 1.0 - (coords_x / (self.width * 0.3)))
            if 'right' in self.connected_edges:
                self.continental_plate_potential = np.maximum(self.continental_plate_potential, 1.0 - ((self.width - 1 - coords_x) / (self.width * 0.3)))
            
            self.continental_plate_potential = np.clip(self.continental_plate_potential, 0, 1)

        # 島国モード（接続なし）の場合の処理
        if num_connections == 0:
            print("  - edge_connections is 0, forming the entire map as an island.")
            center_x, center_y = self.width / 2, self.height / 2
            y_coords, x_coords = np.ogrid[0:self.height, 0:self.width]
            # マップ中央から遠いほど値が大きくなるグラデーション（=海になりやすくなる）
            dist_from_center = np.sqrt(((x_coords - center_x) / (self.width))**2 + ((y_coords - center_y) / (self.height))**2)
            island_gradient = dist_from_center**1.2 # 指数を調整して影響を強くする
            
            self.base_noise -= island_gradient * 1.2
            self.base_noise = (self.base_noise - np.min(self.base_noise)) / (np.max(self.base_noise) - np.min(self.base_noise))


    def _place_main_cores(self):
        """V87-MOD: Places main cores respecting continental plates and revised distance."""
        cores = []
        map_diagonal = np.sqrt(self.width**2 + self.height**2)
        
        # --- ★★★ V91修正: 距離計算を指数的に ★★★ ---
        distance_level = self.config['island_distance_level'] # 1 to 5
        # レベルを-2から2の範囲に変換し、指数関数(pow)で効果を増幅
        # レベル1 -> 1.5^-2 ≒ 0.44 (短い)
        # レベル3 -> 1.5^0 = 1.0 (標準)
        # レベル5 -> 1.5^2 = 2.25 (長い)
        level_effect = pow(1.5, distance_level - 3)
        
        base_dist_multiplier = 0.15 / (self.config['land_ratio']**0.5)
        min_dist_multiplier = base_dist_multiplier * level_effect
        min_dist = map_diagonal * np.clip(min_dist_multiplier, 0.05, 0.9) # 上限も広げる
        # --- ★★★ END OF V91修正 ★★★ ---
        
        print(f"  - Target minimum distance for island cores: {min_dist:.2f} (Level effect: {level_effect:.2f})")

        # --- ★★★ V87修正: コア配置可能エリアの限定 ★★★ ---
        # 大陸プレートの上には島のコアを配置しない
        # また、マップの端ギリギリも避ける
        pad_x, pad_y = int(self.width * 0.1), int(self.height * 0.1)
        valid_placement_mask = np.zeros_like(self.base_noise, dtype=bool)
        valid_placement_mask[pad_y:self.height-pad_y, pad_x:self.width-pad_x] = True
        
        # 大陸プレートが存在する場合は、その上も配置不可エリアとする
        if hasattr(self, 'continental_plate_mask') and np.any(self.continental_plate_mask):
             valid_placement_mask &= ~binary_dilation(self.continental_plate_mask, iterations=20)
        
        valid_y, valid_x = np.where(valid_placement_mask)
        if len(valid_y) == 0:
            print("  - FATAL: No valid area to place island cores. Check edge_connections and land_ratio.")
            return []
        # --- ★★★ END OF V87修正 ★★★ ---

        for i in range(self.config['land_core_count']):
            is_placed = False
            for _ in range(500): # 500回試行
                # 配置可能エリアからランダムに候補を選択
                idx = random.randint(0, len(valid_y) - 1)
                candidate = (valid_x[idx], valid_y[idx])
                
                if not cores:
                    cores.append(candidate)
                    is_placed = True
                    break
                
                is_far_enough = all(
                    ((candidate[0] - core[0])**2 + (candidate[1] - core[1])**2) >= min_dist**2
                    for core in cores
                )
                
                if is_far_enough:
                    cores.append(candidate)
                    is_placed = True
                    break

            if is_placed:
                 print(f"    - Placed main core {i+1} at {cores[-1]}.")
            else:
                print(f"  - Warning: Could not place main core {i+1} satisfying distance. Placing randomly in valid area.")
                idx = random.randint(0, len(valid_y) - 1)
                cores.append((valid_x[idx], valid_y[idx]))

        return cores

 

    def _create_island_skeletons(self):
        print("  - Generating island skeletons...")
        skeletons = []
        main_cores = self._place_main_cores()
        if not main_cores: return []
        for i, (main_cx, main_cy) in enumerate(main_cores):
            skeleton = [(main_cx, main_cy)]
            num_sub_cores = random.randint(2, 5)
            max_radius = min(self.width, self.height) / (len(main_cores) * 1.5 + 2)
            for _ in range(num_sub_cores):
                angle = random.uniform(0, 2 * np.pi)
                radius = random.uniform(max_radius * 0.2, max_radius)
                sc_x = int(main_cx + np.cos(angle) * radius)
                sc_y = int(main_cy + np.sin(angle) * radius)
                sc_x = np.clip(sc_x, 0, self.width - 1)
                sc_y = np.clip(sc_y, 0, self.height - 1)
                skeleton.append((sc_x, sc_y))
            skeletons.append(skeleton)
            print(f"    - Island {i+1} skeleton created with {len(skeleton)} sub-cores.")
        return skeletons

    def _assign_ridge_heights_v54(self, peaks, ridge_network, base_max_peak_h=None):
        """V54-MOD: Assigns varied heights to peaks and ridges, accepting a base height."""
        print("  - Assigning elevation to sharp ridges (V54 - Varied Heights)...")
        ridge_height_map = np.zeros_like(self.height_map, dtype=float)
        ridge_mask = np.zeros_like(self.height_map, dtype=bool)
        
        if base_max_peak_h is None:
            base_max_peak_h = 30 + self.config['mountain_level'] * 15
        
        for px, py in peaks:
            peak_height_multiplier = random.uniform(0.8, 1.2)
            max_peak_h = base_max_peak_h * peak_height_multiplier
            ridge_height_map[py, px] = max_peak_h
            ridge_mask[py, px] = True
            
        ridge_noise_scale = 150.0
        for p1, p2 in ridge_network:
            x1, y1 = p1
            x2, y2 = p2
            length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            if length == 0: continue
            h1 = ridge_height_map[y1, x1]
            h2 = ridge_height_map[y2, x2]
            for i in range(int(length) + 1):
                t = i / length
                x = int(x1 + t * (x2 - x1))
                y = int(y1 + t * (y2 - y1))
                if 0 <= x < self.width and 0 <= y < self.height:
                    interp_h = h1 * (1 - t) + h2 * t
                    saddle_factor = 1.0 - (0.6 * np.sin(t * np.pi))
                    noise_val = snoise2(x / ridge_noise_scale, y / ridge_noise_scale, octaves=4, base=self.seed + 100)
                    height = interp_h * saddle_factor * (0.95 + (noise_val + 1) / 2 * 0.1)
                    if ridge_height_map[y, x] == 0:
                        ridge_height_map[y, x] = height
                    ridge_mask[y, x] = True
        return ridge_height_map, ridge_mask

    def _shape_slopes_by_warping_v66(self, ridge_height_map, mountain_zone, ridge_mask):
        """
        V66: Generates mountain slopes using a distance-based approach combined with domain warping.
        This method is designed to prevent the formation of large, flat plateaus.
        """
        print("  - V66: Shaping slopes with distance transform and domain warping...")
        if not np.any(ridge_mask):
            return np.zeros_like(self.height_map, dtype=np.int16)

        from scipy.ndimage import map_coordinates

        dist_from_ridge, indices = distance_transform_edt(~ridge_mask, return_indices=True)
        nearest_ridge_height_map = ridge_height_map[indices[0], indices[1]]

        slope_gradient = 0.7 + (self.config['mountain_level'] * 0.1)
        base_mountain_map = nearest_ridge_height_map - (dist_from_ridge * slope_gradient)

        print("    - Applying large-scale domain warping...")
        warp_scale = 220.0
        warp_strength = 50.0 + (self.config['mountain_level'] * 5.0)

        warp_noise_x = self._create_detail_noise(scale=warp_scale, octaves=5, base_offset=601)
        warp_noise_y = self._create_detail_noise(scale=warp_scale, octaves=5, base_offset=602)
        
        y_coords, x_coords = np.mgrid[0:self.height, 0:self.width]

        warped_y = y_coords + (warp_noise_y - 0.5) * warp_strength
        warped_x = x_coords + (warp_noise_x - 0.5) * warp_strength
        
        warped_map = map_coordinates(base_mountain_map, [warped_y, warped_x], order=1, mode='reflect')

        print("    - Adding multi-layered noise for detail...")
        medium_noise = self._create_detail_noise(scale=85.0, octaves=6, base_offset=603)
        medium_strength = (10.0 + self.config['mountain_level'] * 3.0)
        detailed_map = warped_map + (medium_noise - 0.5) * medium_strength

        small_noise = self._create_detail_noise(scale=30.0, octaves=7, base_offset=604)
        small_strength = (3.0 + self.config['mountain_level'])
        detailed_map += (small_noise - 0.5) * small_strength
        
        final_map = np.zeros_like(self.height_map, dtype=float)
        final_map[mountain_zone] = detailed_map[mountain_zone]
        final_map = np.maximum(0, final_map)

        final_map[ridge_mask] = ridge_height_map[ridge_mask]
        
        final_map = gaussian_filter(final_map, sigma=0.5)

        return final_map.astype(np.int16)

    def _create_ridge_network(self, mountain_zone):
        """V54: Builds a sparse, varied ridge network with controlled connectivity."""
        print("  - Building ridge network (V54 - Sparse & Varied)...")
        num_peaks = int((np.sum(mountain_zone) / (256*256)) * 35 * (self.config['mountain_level'] / 2.0))
        if num_peaks < 2: return [], []
        
        peak_candidates_y, peak_candidates_x = np.where(mountain_zone)
        if len(peak_candidates_y) < num_peaks: return [], []
        
        indices = np.random.choice(len(peak_candidates_y), num_peaks, replace=False)
        peaks = list(zip(peak_candidates_x[indices], peak_candidates_y[indices]))
        if len(peaks) < 2: return [], []

        from scipy.spatial import cKDTree
        points = np.array(peaks)
        kdtree = cKDTree(points)
        
        ridge_network = set()
        for i, p1 in enumerate(points):
            distances, neighbor_indices = kdtree.query(p1, k=3)
            
            if len(neighbor_indices) > 1:
                p2_idx = neighbor_indices[1]
                edge = tuple(sorted((i, p2_idx)))
                ridge_network.add(edge)

            if len(neighbor_indices) > 2 and random.random() < 0.35:
                p3_idx = neighbor_indices[2]
                edge = tuple(sorted((i, p3_idx)))
                ridge_network.add(edge)

        final_ridge_network = [(peaks[p1_idx], peaks[p2_idx]) for p1_idx, p2_idx in ridge_network]
        print(f"    - Generated {len(peaks)} peaks and {len(final_ridge_network)} ridges.")
        return peaks, final_ridge_network

    def _process_coastline(self):
        print("Step 5: Processing coastline")
        if not np.any(self.land_mask): return
        coast_pixels = self._find_coastline_pixels()
        if not coast_pixels: return
        coast_zones = self._segment_coastline(coast_pixels, num_zones_per_feature=3)
        self._assign_zone_types(coast_zones, self.unconnected_edges)
        for zone in coast_zones:
            if zone['type'] == 'rias': self._generate_rias_coast(zone)
            elif zone['type'] == 'sandy': self._generate_sandy_beach(zone)
            elif zone['type'] == 'cliff': self._generate_cliff_coast(zone)
        self.land_mask = binary_opening(self.land_mask, iterations=1)
        print(f"  - Land ratio (after processing): {np.sum(self.land_mask) / (self.width * self.height):.2f}")

    def _find_coastline_pixels(self):
        eroded_land = binary_opening(self.land_mask, structure=np.ones((3,3)), iterations=1)
        coastline = self.land_mask & ~eroded_land
        return list(zip(*np.where(coastline)))

    def _segment_coastline(self, pixels, num_zones_per_feature=3):
        pixel_map = np.zeros((self.height, self.width), dtype=np.uint8)
        for y, x in pixels: pixel_map[y, x] = 255
        labeled_map, num_features = label(pixel_map)
        all_zones = []
        for i in range(1, num_features + 1):
            segment_pixels = list(zip(*np.where(labeled_map == i)))
            if len(segment_pixels) < 100: continue
            segment_length = len(segment_pixels) // num_zones_per_feature
            if segment_length < 50: continue
            for j in range(0, len(segment_pixels), segment_length):
                zone_pixels = segment_pixels[j:j + segment_length]
                if zone_pixels: all_zones.append({'pixels': zone_pixels, 'type': 'default'})
        return all_zones

    def _assign_zone_types(self, zones, unconnected_edges):
        print("... Assigning coastline types")
        edge_buffer_threshold = 250
        for zone in zones:
            avg_y, avg_x = np.mean(zone['pixels'], axis=0)
            is_near_unconnected_edge = False
            if 'top' in unconnected_edges and avg_y < edge_buffer_threshold: is_near_unconnected_edge = True
            if 'bottom' in unconnected_edges and avg_y > self.height - edge_buffer_threshold: is_near_unconnected_edge = True
            if 'left' in unconnected_edges and avg_x < edge_buffer_threshold: is_near_unconnected_edge = True
            if 'right' in unconnected_edges and avg_x > self.width - edge_buffer_threshold: is_near_unconnected_edge = True
            if is_near_unconnected_edge:
                complex_weights = {'sandy': 1, 'cliff': 5, 'rias': 5}
                zone['type'] = random.choices(list(complex_weights.keys()), weights=list(complex_weights.values()), k=1)[0]
            else:
                level = self.config['coastline_complexity_level']
                weights = {'sandy': 6 - level, 'cliff': max(0, level - 2), 'rias': max(0, level - 1)}
                types = list(weights.keys())
                if sum(weights.values()) == 0: weights = {'sandy':1, 'cliff':1, 'rias':1}
                zone['type'] = random.choices(types, weights=list(weights.values()), k=1)[0]

    def _generate_rias_coast(self, zone):
        zone_mask = np.zeros_like(self.land_mask, dtype=np.uint8)
        for y, x in zone['pixels']: cv2.circle(zone_mask, (x, y), 40, 255, -1)
        mountain_noise = self._create_detail_noise(scale=80.0, octaves=6, base_offset=4)
        erosion_level = mountain_noise * 0.4 + 0.35
        self.land_mask[(mountain_noise < erosion_level) & (zone_mask > 0)] = False

    def _generate_sandy_beach(self, zone):
        zone_mask = np.zeros_like(self.land_mask, dtype=np.uint8)
        for y, x in zone['pixels']: cv2.circle(zone_mask, (x, y), 50, 255, -1)
        self.land_mask = binary_closing(self.land_mask, mask=zone_mask, structure=np.ones((7,7)), iterations=3)
        self.land_mask = binary_opening(self.land_mask, mask=zone_mask, structure=np.ones((3,3)), iterations=2)

    def _generate_cliff_coast(self, zone):
        zone_mask = np.zeros_like(self.land_mask, dtype=np.uint8)
        for y, x in zone['pixels']: cv2.circle(zone_mask, (x, y), 30, 255, -1)
        dist_from_sea = distance_transform_edt(self.land_mask)
        cliff_line = (dist_from_sea > 4) & (dist_from_sea < 7) & (zone_mask > 0)
        self.height_map[cliff_line] += 8
        self.land_mask[cliff_line] = True

    def _save_debug_mask(self, output_dir):
        print("... Saving debug mask image")
        filename = f"debug_mask_{self.timestamp}.png"
        output_path = os.path.join(output_dir, filename)
        mask_image = Image.fromarray(self.land_mask.astype(np.uint8) * 255, 'L')
        mask_image.save(output_path)

    def _create_detail_noise(self, scale, octaves, base_offset):
        detail_noise = np.zeros((self.height, self.width))
        for y in range(self.height):
            for x in range(self.width):
                detail_noise[y][x] = snoise2(x/scale, y/scale, octaves=octaves, base=self.seed + base_offset)
        return (detail_noise - np.min(detail_noise)) / (np.max(detail_noise) - np.min(detail_noise))

    def _create_color_representation(self):
        color_map = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        g = self.grayscale_map

        # Define colors
        COLOR_DEEPEST_SEA = np.array([10, 20, 100])
        COLOR_SHALLOW_SEA = np.array([80, 120, 200])
        COLOR_SANDY_BEACH = np.array([210, 200, 150])
        COLOR_PLAINS = np.array([50, 180, 50])
        COLOR_HIGH_MOUNTAINS = np.array([140, 110, 80])
        COLOR_HIGHEST_PEAK = np.array([255, 255, 255])

        # Sea (g <= 68)
        sea_mask = g <= 68
        if np.any(sea_mask):
            sea_values = g[sea_mask].astype(float)
            t = sea_values / 68.0
            color_map[sea_mask] = (COLOR_DEEPEST_SEA * (1 - t[:, np.newaxis]) + COLOR_SHALLOW_SEA * t[:, np.newaxis]).astype(np.uint8)

        # Coastline (g == 69)
        color_map[g == 69] = COLOR_SANDY_BEACH

        # Land (g >= 70)
        land_mask = g >= 70
        if np.any(land_mask):
            land_values = g[land_mask].astype(float)
            # Map grayscale 70-255 to t=0-1
            t = np.clip((land_values - 70.0) / 185.0, 0, 1)
            
            # Gradation from Plains -> High Mountains -> Peak
            grad_map = np.zeros((len(t), 3))
            
            # 0.0 to 0.5: Plains to High Mountains
            mask_low = t <= 0.5
            t_low = t[mask_low] * 2
            grad_map[mask_low] = COLOR_PLAINS * (1 - t_low[:, np.newaxis]) + COLOR_HIGH_MOUNTAINS * t_low[:, np.newaxis]

            # 0.5 to 1.0: High Mountains to Highest Peak
            mask_high = t > 0.5
            t_high = (t[mask_high] - 0.5) * 2
            grad_map[mask_high] = COLOR_HIGH_MOUNTAINS * (1 - t_high[:, np.newaxis]) + COLOR_HIGHEST_PEAK * t_high[:, np.newaxis]

            color_map[land_mask] = np.clip(grad_map, 0, 255).astype(np.uint8)

        return color_map

    def save_final_outputs(self, output_dir):
        print("\n--- Saving Final Outputs ---")
        os.makedirs(output_dir, exist_ok=True)
        filename_gray = f"generated_map_{self.timestamp}.png"
        path_gray = os.path.join(output_dir, filename_gray)
        Image.fromarray(self.grayscale_map, 'L').save(path_gray)
        print(f"  - Saved grayscale map: {path_gray}")
        color_map_data = self._create_color_representation()
        filename_color = f"island_map_{self.timestamp}.png"
        path_color = os.path.join(output_dir, filename_color)
        Image.fromarray(color_map_data, 'RGB').save(path_color)
        print(f"  - Saved color map: {path_color}")


if __name__ == '__main__':
    # このパスはご自身の環境に合わせて修正してください
    CONFIG_FILE = r'C:\Users\three\mapV2\config.json'
    OUTPUT_DIR = r'C:\Users\three\mapV2\png'

    print("--- Generating map with V101 specification (Full Features) ---")
    generator = MapGenerator(CONFIG_FILE)
    generator.timestamp = f"{generator.timestamp}_V101_full"
    generator.generate_map(OUTPUT_DIR)
    generator.save_final_outputs(OUTPUT_DIR)
    print("\n--- V101 map generation complete ---")
