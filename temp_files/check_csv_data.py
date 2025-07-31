import csv

with open('production_freecad_random_fem_evaluation.csv', 'r') as f:
    reader = csv.DictReader(f)
    total = 0
    valid = 0
    invalid_rows = []
    
    for i, row in enumerate(reader, 1):
        total += 1
        
        # safety_factorとco2_per_sqmの両方が有効かチェック
        safety_ok = False
        co2_ok = False
        
        if row.get('safety_factor') and row['safety_factor'] != 'nan' and row['safety_factor'] != '':
            try:
                float(row['safety_factor'])
                safety_ok = True
            except:
                pass
                
        if row.get('co2_per_sqm') and row['co2_per_sqm'] != 'nan' and row['co2_per_sqm'] != '':
            try:
                float(row['co2_per_sqm'])
                co2_ok = True
            except:
                pass
        
        if safety_ok and co2_ok:
            valid += 1
        else:
            invalid_rows.append((i, row.get('safety_factor', ''), row.get('co2_per_sqm', '')))
    
    print(f'総データ行数（ヘッダー除く）: {total}')
    print(f'有効データ行数: {valid}')
    print(f'除外データ行数: {total - valid}')
    
    if invalid_rows:
        print('\n除外された行:')
        for row_num, safety, co2 in invalid_rows[:5]:
            print(f'  行{row_num}: safety_factor={safety}, co2_per_sqm={co2}')