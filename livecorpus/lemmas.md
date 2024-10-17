Поскольку не работала веб-версия Mystem, всю обработку я производил через API программы на Python (библиотека pymystem3). С помощью нескольких скриптов удалось соединить итоговый файл с разметкой (разве что для морфологического анализа и лемм пришлось сделать две отдельные таблицы в pandas, экспортировав их в два файла .tsv, которые я потом объединил в один вручную через текстовый редактор). <br/><br/><br/>
Скрипт 1: <br/>
import pandas as pd<br/>
from pymystem3 import Mystem<br/><br/>

df = pd.read_csv('exported_words.csv', sep='	')<br/>
mystem = Mystem()<br/><br/><br/>


def lemmatize_word(row):<br/>
    word = row['word']<br/>
    lemma = mystem.lemmatize(word)[0]<br/>
    return lemma<br/>


df['lemma'] = df.apply(lemmatize_word, axis=1)<br/>

df.to_csv('exported_words_with_lemmas.csv', encoding='utf-8')<br/>
<br/>
Скрипт 2:<br/>
import pandas as pd<br/>
from pymystem3 import Mystem<br/><br/>

df = pd.read_csv('exported_words_with_lemmas.csv', sep=',')<br/>
mystem = Mystem()<br/><br/>


def analyze_word(row):<br/>
    word = row['word']<br/>
    try:<br/>
        analysis = mystem.analyze(word)[0]['analysis'][0]['gr']<br/>
        return analysis<br/>
    except:<br/>
        return ' '<br/><br/><br/>


print(df.head())<br/>
df['analysis'] = df.apply(analyze_word, axis=1)<br/>
df.to_csv('exported_words_analyzed.csv', encoding='utf-8')<br/>
<br/>
Скрипт 3:<br/>
import pandas as pd<br/>

df = pd.read_csv('exported_words_analyzed.csv', encoding='utf-8')<br/>


def add_lemma_layer_name(row):<br/>
    layer_name = row['layer']<br/>
    suffix = layer_name.split('@')[1]<br/>
    new_name = 'lemma@' + suffix<br/>
    return new_name<br/>


def add_analysis_layer_name(row):<br/>
    layer_name = row['layer']<br/>
    suffix = layer_name.split('@')[1]<br/>
    new_name = 'morph@' + suffix<br/>
    return new_name<br/>


df['lemma_layer_name'] = df.apply(add_lemma_layer_name, axis=1)<br/>
df['morph_layer_name'] = df.apply(add_analysis_layer_name, axis=1)<br/>

df_lemma = df[['lemma_layer_name', 'speaker', 'start', 'finish', 'lemma']]<br/>
df_lemma.to_csv('lemma_words_elan.tsv', encoding='utf-8', header=False, index=False, sep='\t')<br/>
df_morph = df[['morph_layer_name', 'speaker', 'start', 'finish', 'analysis']]<br/>
df_morph.to_csv('morph_words_elan.tsv', encoding='utf-8', header=False, index=False, sep='\t')<br/>
<br/>
С лемматизацией и разметкой анализатор справился довольно хорошо. Из ошибок можно отметить то, что наречие "прямо" (в контексте "прямо как тренер очень хороша") он лемматизировал до прилагательного "прямой". Также он не смог лемматизировать форму "ШЧРе" (предложный падеж от склонявшейся аббревиатуры "ШЧР" - Школьный Чемпионат России), при этом саму форму он разметил как существительное, но, видимо, приписал иное склонение.
