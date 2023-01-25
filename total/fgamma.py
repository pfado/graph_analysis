import cugraph
import cudf

import numpy as np
import math
import os
import matplotlib.pyplot as plt

from tqdm import tqdm
from scipy.optimize import bisect
from collections import Counter
from scipy.stats import t


def frequencies(df):
    a = df.value_counts(subset=['Vertex'])
    hitcount = cudf.DataFrame({'Vertex' : a.index.to_arrow()[0].to_pylist(), 'degree': a.values})
    c = Counter(hitcount['degree'].to_arrow().to_pylist())
    return cudf.DataFrame({
            'Grado': c.keys(),
            'Recuento': c.values()
            }).sort_values(by='Grado')



def get_gamma(df):
    
    if df.empty:
        return np.NaN

    x = df['Grado'].to_numpy()
    y = df['Recuento'].to_numpy()

    if len(x) < 10:
        return np.NaN

    try:
        def f(gamma):

            s_xx = sum(x ** (-2 * gamma))
            s_xy = sum(y * (x ** -gamma))

            s_lxy = sum(y * np.log(x) * (x ** -gamma))
            s_lxx = sum(np.log(x) * (x ** (-2 * gamma)))
            return s_lxy - (s_xy / s_xx) * s_lxx

        a = 0
        b = 10

        return bisect(f, a, b)

    except: f'Error while obtaining gamma value'
    
def get_beta(df, gamma):
    
    if df.empty or gamma is None:
        return np.NaN
    
    x = df['Grado'].to_numpy()
    y = df['Recuento'].to_numpy()
    
    
    s_xx = sum(x ** (-2 * gamma))
    s_xy = sum(y * (x ** -gamma))
    
    return np.log(s_xy/s_xx)

def mse_regression(df):
        
    x = np.log(df['Grado'].to_numpy())
    y = np.log(df['Recuento'].to_numpy())
    
    gamma = get_gamma(df)
    beta = get_beta(df, gamma)
    
    if gamma is None:
        return np.NaN, np.NaN, np.NaN
    
    # R-squared    
    x_bar = np.mean(x)
    y_bar = np.mean(y)
    
    ss_u = np.sum((x-x_bar)*(y-y_bar))
    ss_l = np.sqrt(np.sum((x-x_bar)**2)*np.sum((y-y_bar)**2))
    
    r_squared = ss_u/ss_l

    
    return gamma, beta, r_squared






if __name__ == "__main__":

    
    ###############
    # Change here to your path where the matrix lists are located (mind that you will have to change the code for Windows paths)
    input_files = 'matrices_sin_filt'
    output_file_name = 'regresion_filtradas_tot'
    ##############
    # percentages = [5 * (10 - i) for i in range(0,10)] # [10,50]
    percentages = [5 * (20 - i) for i in range(1, 20)] # [5, 95]
    
    fields = []
    data = []
    
    for file in os.listdir(input_files):
        if file == '.ipynb_checkpoints':
            continue
        file_name = file.split(os.sep)[-1].split('-')[-1].split('.')[0]
                
        print('\n' + file_name + '\n')

        df = cudf.read_csv(
            filepath_or_buffer=f'{input_files}/{file}',
            header=None,
            names=['Source', 'Target', 'Weight'],
            sep=' ')
        
        if df.empty: 
            continue
            
        fields = []

        list_weights = df['Weight'].drop_duplicates().to_arrow().to_pylist()
        nodes_weight = cudf.concat([
            df[['Source', 'Weight']].rename(columns={"Source": "Vertex", "Weight": "Weight"}),
            df[['Target', 'Weight']].rename(columns={"Target": "Vertex", "Weight": "Weight"})
                            ])
        node_list = nodes_weight['Vertex'].drop_duplicates().to_arrow().to_pylist()


        for weight in tqdm(list_weights):
            n = len(nodes_weight[nodes_weight['Weight'] >= weight])
            fields.append({
                'Weight': weight,
                'N': n,
                'n%': (n / len(nodes_weight)) * 100
                })


        df_percentages = cudf.DataFrame(fields).sort_values(by='n%', ascending=False)
        if df_percentages.empty: 
            continue
        weight_df = cudf.DataFrame()

        for percentage in percentages:
            val_list = np.abs(df_percentages['n%'] - percentage).to_arrow().to_pylist()
            val_index = val_list.index(
            min(val_list)
            )
            value = float(df_percentages['n%'].values[val_index])
            weight_df = cudf.concat([
                       weight_df,
                       df_percentages[df_percentages['n%'] == value]

            ])
          

        weight_df['closest_n%'] = percentages

        gamma, beta, r_sq = mse_regression(frequencies(nodes_weight))
        data.append({
                'Gamma': gamma,
                'Beta': beta,
                'R_Square':r_sq,
                'Weight': min(list_weights),
                'Percentage': 0,
                'N_edges':len(nodes_weight),
                'N_nodes':len(node_list),
                'File': file_name
            })
        
        for percentage in percentages:

            weight = weight_df[weight_df['closest_n%'] == percentage]['Weight'].to_numpy()[0]
            nodes = nodes_weight[nodes_weight['Weight'] >= weight]
            
            freq = frequencies(nodes_weight[nodes_weight['Weight'] >= weight])
                
            gamma, beta, r_squared = mse_regression(freq)
            
            data.append({
                'Gamma': gamma,
                'Beta': beta,
                'R_Square':r_squared,
                'Weight': weight,
                'Percentage': percentage,
                'N_edges':len(nodes_weight)/2,
                'N_nodes':len(nodes),
                'File': file_name
            })

    df_tot = cudf.DataFrame(data)

    df_tot.to_csv(
        path_or_buf=f'{output_file_name}.txt',
        index=False,
        sep='\t'
    )