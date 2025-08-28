# test_launch_with_df.py

import pandas as pd
import numpy as np
from main import main

def run_test():
    """
    サンプルDataFrameを作成し、それを引数としてCalciteを起動するテスト。
    """
    # 1. テスト用のサンプルDataFrameを作成
    #    - `point_plot_sample.csv` を模したデータ構造
    data = {
        'Timepoint': ['0h']*3 + ['6h']*3 + ['12h']*3 + ['24h']*3 + \
                     ['0h']*3 + ['6h']*3 + ['12h']*3 + ['24h']*3,
        'Genotype': ['Wildtype']*12 + ['Mutant']*12,
        'Response': np.concatenate([
            np.random.normal(10.8, 0.4, 3), # 0h, Wildtype
            np.random.normal(15.2, 0.4, 3), # 6h, Wildtype
            np.random.normal(19.2, 0.3, 3), # 12h, Wildtype
            np.random.normal(20.1, 0.4, 3), # 24h, Wildtype
            np.random.normal(10.2, 0.4, 3), # 0h, Mutant
            np.random.normal(11.8, 0.3, 3), # 6h, Mutant
            np.random.normal(10.8, 0.4, 3), # 12h, Mutant
            np.random.normal(9.8,  0.3, 3), # 24h, Mutant
        ])
    }
    sample_df = pd.DataFrame(data)
    
    # --- デバッグ用print ---
    print("--- Launching Calcite with the following DataFrame: ---")
    print(sample_df)
    print("----------------------------------------------------")
    
    # 2. 作成したDataFrameを引数として、Calciteのmain関数を呼び出す
    #    main.pyのmain関数を直接インポートして使用します。
    main(data=sample_df)

if __name__ == "__main__":
    run_test()