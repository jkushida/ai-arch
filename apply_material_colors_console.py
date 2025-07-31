# FreeCAD Pythonコンソール用 材料色適用スクリプト
# 使い方: FreeCADでFCStdファイルを開いた後、Pythonコンソールでこのスクリプトを実行

doc = App.ActiveDocument
if doc:
    # 材料色の定義
    material_colors = {
        0: (0.8, 0.8, 0.8),    # コンクリート（グレー）
        1: (0.55, 0.35, 0.2)   # 木材（茶色）
    }
    
    # 建物パーツのリスト（これらのみ表示）
    building_parts = ['Staircase', 'Foundation', 'Floor1', 'Floor2', 
                      'Columns', 'Walls', 'RoofSlab', 'Balcony']
    
    # 各建物パーツの材料設定を自動検出（ラベルから推測）
    # デフォルトはコンクリート(0)、必要に応じて手動で変更
    part_materials = {
        'Columns': 0,
        'Floor1': 0,
        'Floor2': 0,
        'RoofSlab': 0,
        'Walls': 0,
        'Balcony': 0,
        'Foundation': 0,
        'Staircase': 0
    }
    
    # ドキュメント名から材料パターンを推測
    doc_name = doc.Name
    if "全木材" in doc_name:
        # 全て木材
        for key in part_materials:
            part_materials[key] = 1
    elif "ハイブリッド1" in doc_name:
        # コンクリート柱・1階床、木材2階床・屋根・壁
        part_materials.update({
            'Columns': 0,
            'Floor1': 0,
            'Floor2': 1,
            'RoofSlab': 1,
            'Walls': 1,
            'Balcony': 0
        })
    elif "ハイブリッド2" in doc_name:
        # 木材柱、コンクリート1階床・壁、木材2階床・屋根・バルコニー
        part_materials.update({
            'Columns': 1,
            'Floor1': 0,
            'Floor2': 1,
            'RoofSlab': 1,
            'Walls': 0,
            'Balcony': 1
        })
    
    print("=== 材料色適用開始 ===")
    applied_count = 0
    visible_count = 0
    hidden_count = 0
    
    # 全オブジェクトを処理
    for obj in doc.Objects:
        # ViewObjectが存在する場合のみ処理
        if hasattr(obj, 'ViewObject') and obj.ViewObject:
            # 建物パーツのみ可視化、それ以外は非表示
            if hasattr(obj.ViewObject, 'Visibility'):
                if obj.Label in building_parts:
                    obj.ViewObject.Visibility = True
                    visible_count += 1
                    
                    # 建物パーツの色を適用
                    if obj.Label in part_materials:
                        material = part_materials[obj.Label]
                        color = material_colors[material]
                        material_name = '木材' if material == 1 else 'コンクリート'
                        
                        try:
                            obj.ViewObject.ShapeColor = color
                            obj.ViewObject.Transparency = 0
                            print(f"✓ {obj.Label}: {material_name}色を適用 {color}")
                            applied_count += 1
                        except Exception as e:
                            print(f"✗ {obj.Label}: 色の適用に失敗 - {str(e)}")
                else:
                    obj.ViewObject.Visibility = False
                    hidden_count += 1
    
    # ドキュメントを再計算
    doc.recompute()
    
    # GUIを更新
    if hasattr(FreeCADGui, 'updateGui'):
        Gui.updateGui()
    
    # ビューを調整（全体表示＆アイソメトリック）
    try:
        Gui.SendMsgToActiveView("ViewFit")
        Gui.activeDocument().activeView().viewIsometric()
        print("\nビューを調整しました（全体表示・アイソメトリック）")
    except Exception as e:
        print(f"\nビュー調整中にエラー: {str(e)}")
    
    print(f"\n=== 処理完了 ===")
    print(f"色を適用したパーツ: {applied_count}個")
    print(f"可視化した建物パーツ: {visible_count}個")
    print(f"非表示にしたオブジェクト: {hidden_count}個")
    print(f"現在のドキュメント: {doc_name}")
    
    # 手動で材料を変更する場合の例
    print("\n材料を手動で変更する場合の例:")
    print("part_materials['Columns'] = 1  # 柱を木材に変更")
    print("その後、このスクリプトを再実行してください")
else:
    print("エラー: アクティブなドキュメントがありません")
    print("FreeCADでFCStdファイルを開いてから実行してください")