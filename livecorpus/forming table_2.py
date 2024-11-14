import pandas as pd

df = pd.read_csv('sem_annotated_elan_data.tsv', sep='\t', encoding='utf-8')
print(df.info())

def add_sem_layer_name(row):
    layer_name = row['layer']
    suffix = layer_name.split('@')[1]
    new_name = 'semantic_annotation@' + suffix
    return new_name


df['semantic_layer_name'] = df.apply(add_sem_layer_name, axis=1)

df_lemma = df[['semantic_layer_name', 'speaker', 'start', 'finish', 'semantic_annotation']]
df_lemma.to_csv('semantic_annotation_elan.tsv', encoding='utf-8', header=False, index=False, sep='\t')
