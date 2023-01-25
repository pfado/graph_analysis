import cugraph
import cudf

import numpy as np
import os

from tqdm import tqdm


def clustering(G):
    degree = G.in_degree()
    
    clusters = degree.merge(cugraph.triangle_count(G))
    clusters = clusters[clusters['counts'] >= 1]
    
    return (clusters['counts']/(clusters['degree']*(clusters['degree'] - 1))).sum()

def distance(G, nodes):
    dist = 0
    inv_dist = 0

    for node in tqdm(nodes):
        distances = cugraph.sssp(G, node)
        dist += distances[distances['predecessor'] > -1]['distance'].sum()/(len(nodes)*(len(nodes) - 1))
        inv_dist += (1/distances[distances['predecessor'] > -1]['distance']).sum()/(len(nodes)*(len(nodes) - 1))
    return dist, inv_dist


def shannon_entropy(G):
    hitcount = G.in_degree()
    frequencies = hitcount[hitcount['degree'] > 0]['degree'].value_counts().to_numpy()

    p_k = frequencies/sum(frequencies)
    return sum(-p_k * np.log(p_k))



if __name__ == "__main__":

    ###############
    # Change here to your path where the matrix lists are located (mind that you will have to change the code for Windows paths)
    input_files = 'matrices_sin_filt'
    output_files = 'parametros_matrices_no_filtradas'
    ##############
    # percentages = [5 * (10 - i) for i in range(0,10)] # [10,50]
    percentages = [5 * (20 - i) for i in range(1, 20)] # [5, 95]
    
    for file in os.listdir(input_files):
        if file == '.ipynb_checkpoints':
            continue
        
        file_name = file.split(os.sep)[-1].split('-')[-1].split('.')[0]
        
        print('\n\n' + file_name + '\n')
        if os.path.isfile(f'{output_files}/params-{file_name}.txt'):
            continue

        df = cudf.read_csv(
            filepath_or_buffer=f'{input_files}/{file}',
            header=None,
            names=['Source', 'Target', 'Weight'],
            sep=' ')
        if df.empty:
            continue
        
        df = df[df['Weight'] > 0.800]
        
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
        
        def get_params():
    
            print('##### BEGING THE PROCESS OF OBTAINING THE NETWORK PARAMETERS USING DIFFERENT THRESHOLDS ########')
            print(f'\n 100% - Weight threshold: {min(list_weights):.3f}')
    
            G = cugraph.Graph()
            G.from_cudf_edgelist(df, source='Source', destination='Target', renumber=False)

            clustering_zero = clustering(G)
            distance_zero, efficiency_zero = distance(G, node_list)
            shannon_zero = shannon_entropy(G)

            fields = [{
                      'Percentage': 100,
                     'Real Percentage': 100,
                      'Number of voxels': len(node_list),
                      'Weight': min(list_weights),
                      'Distance': distance_zero,
                      'Clustering': clustering_zero,
                      'Global Efficiency': efficiency_zero,
                      'Shannon Entropy': shannon_zero
                  }]

            G.clear()

            if weight_df.empty:
                return cudf.DataFrame()

            for percentage in percentages:
        
                weight = weight_df[weight_df['closest_n%'] == percentage]['Weight'].to_numpy()[0]
                print(f'\n {percentage}% - Weight threshold: {weight:.3f}')
                filt_df = df[df['Weight'] >= weight]
                nodes = nodes_weight[nodes_weight['Weight'] >= weight]['Vertex'].drop_duplicates().to_arrow().to_pylist()

                G = cugraph.Graph()
                G.from_cudf_edgelist(filt_df, source='Source', destination='Target', renumber=False)

                if len(G.edges()) < 1:
                    continue
      
                clustering_coeff = clustering(G)
                distance_coeff, efficiency_coeff = distance(G, nodes)
                shannon_coeff = shannon_entropy(G)

                fields.append({
                      'Percentage': percentage,
                      'Real Percentage': weight_df[weight_df['closest_n%'] == percentage]['n%'].to_numpy()[0],
                      'Number of voxels': len(nodes),
                      'Weight': weight_df[weight_df['closest_n%'] == percentage]['Weight'].to_numpy()[0],
                      'Distance': distance_coeff,
                      'Clustering': clustering_coeff,
                      'Global Efficiency': efficiency_coeff,
                      'Shannon Entropy': shannon_coeff
                  })
                G.clear()

                dataframe = cudf.DataFrame(fields)

                if dataframe.empty:
                    return cudf.DataFrame()

                dataframe.to_csv(
                  path_or_buf=f'{output_files}/params-{file_name}.txt',
                  index=False,
                  header=True,
                  sep='\t')

            return dataframe

        get_params()