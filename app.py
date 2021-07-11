from flask import Flask, render_template, request
import re
import pandas as pd
from pymorphy2 import MorphAnalyzer
from more_itertools import unique_everseen

from nltk.tokenize import word_tokenize
import nltk

nltk.download('punkt')
data = pd.read_csv('dataset.csv')

app = Flask(__name__)


# , methods=['get']
@app.route('/', methods=['GET', 'POST'])
def quest():
    return render_template('quest.html')


@app.route('/process', methods=['GET', 'POST'])
def answer_process():
    inquery = request.form.get('inquery')

    def pymorphy_lemmas(text):
        lemmas = []
        text = word_tokenize(text)
        for word in text:
            if word != '.':
                ana = MorphAnalyzer().parse(word)
                lemmas.append(ana[0].normal_form)
        lemmas = ' '.join(lemmas)
        return lemmas

    # эта ищет поиск - нужно найти все предложения, где слово встречается в любой форме

    def search_all(word_input):
        words = pymorphy_lemmas(word_input)
        words = words.split(' ')
        output = []
        for idx, sentence in enumerate(data['lemmas']):
            sen = word_tokenize(sentence)
            for i, word in enumerate(sen):
                if len(words) == 1 and word == words[0]:
                    output.append(idx)
                elif len(words) == 2:
                    try:
                        if word == words[0] and sen[i + 1] == words[1]:
                            output.append(idx)
                    except:
                        pass
                elif len(words) == 3:
                    try:
                        if word == words[0] and sen[i + 1] == words[1] and sen[i + 2] == words[2]:
                            output.append(idx)
                    except:
                        pass
        out = pd.DataFrame()
        out['id'] = data['id'].iloc[output]
        out['text'] = data['text'].iloc[output]
        return out

    # “поиска” - нужно найти предложения только с этой формой
    # NOUN - найти все предложения с существительными

    def search_exact(word_inputs):
        word_inputs = re.sub('"', '', word_inputs)
        words = word_inputs.split(' ')
        output = []
        for idx, sentence in enumerate(data['text']):
            sen = word_tokenize(sentence)
            for i, word in enumerate(sen):
                if len(words) == 1 and word == words[0]:
                    output.append(idx)
                elif len(words) == 2:
                    try:
                        if word == words[0] and sen[i + 1] == words[1]:
                            output.append(idx)
                    except:
                        pass
                elif len(words) == 3:
                    try:
                        if word == words[0] and sen[i + 1] == words[1] and sen[i + 2] == words[2]:
                            output.append(idx)
                    except:
                        pass
        out = pd.DataFrame()
        out['id'] = data['id'].iloc[output]
        out['text'] = data['text'].iloc[output]
        return out

    # search(‘NOUN VERB ADVB’)

    def search_pos(poses_all):
        poses = poses_all.upper()
        ids = []
        texts = []
        if len(poses.split(' ')) > 3:
            print('Эта программа не ищет такие длинные строчки.')
        else:
            for p in data['pos']:
                if poses in p:
                    id = data.loc[data['pos'] == p].index.values
                    ids.append(id[0])
            output = pd.DataFrame()
            output['id'] = data['id'].iloc[ids]
            output['text'] = data['text'].iloc[ids]
            return output

    def search_word_by_pos(word):
        splitted_word = word.split('+')
        word = pymorphy_lemmas(splitted_word[0])
        id_lines = []
        out = []
        fin_id_lines = []
        for line in data['lemmas']:
            if word in line:
                id_line = data.loc[data['lemmas'] == line].index.values
                id_lines.append(id_line[0])
                splitted_line = line.split(' ')
                count_idx = 0
                for w in splitted_line:
                    if w == word:
                        count_idx = count_idx
                    else:
                        count_idx += 1
            for i in id_lines:
                pos_index = 0
                poses = data['pos'][i]
                for pos in poses:
                    if pos == splitted_word[1]:
                        pos_index = pos_index
                    else:
                        pos_index += 1
                    if pos_index == count_idx:
                        out.append(data['text'][i])
                        fin_id_lines.append(id_line[0])
        unique_sentences = list(unique_everseen(out))
        unique_id_lines = list(unique_everseen(fin_id_lines))
        output = pd.DataFrame()
        output['id'] = data['id'].iloc[unique_id_lines]
        output['text'] = unique_sentences
        return output

    def search(input):
        input = input.split()
        output = []
        type_of_input = []  # список, в котором лежат типы элементов инпута
        for i in input:
            if '"' in i:
                i = re.sub('"', '', i)
                output.append(search_exact(i).index.values)
                type_of_input.append('exactform')
            elif '+' in i:
                output.append(search_word_by_pos(i).index.values)
                type_of_input.append('wordbypos')
            elif i.isupper():
                output.append(search_pos(i).index.values)
                type_of_input.append('pos')
            else:
                output.append(search_all(i).index.values)
                type_of_input.append('notexact')
        inter = set(output[0])
        for i in output[1:]:
            inter = inter.intersection(set(i))
        if len(input) == 1:
            inter = [i for i in inter]
            output = pd.DataFrame()
            output['id'] = data['id'].iloc[inter]
            output['text'] = data['text'].iloc[inter]
        else:
            idxs = []
            for index in inter:
                num = 0
                numbers = []
                for el in input:  # берем элемент ввода
                    typeinput = type_of_input[num]  # тип элемента ввода
                    num += 1
                    if typeinput == 'exactform':  # если точная форма, ищем номер элемента в нужной строчке столбца "текст"
                        needtext = data['text'][index]  # ищем нужное предложение
                        text = needtext.split(' ')  # разбиваем текст, чтобы вытащить номер нужного слова
                        number = text.index(
                            el)  # добавляем номер элемента ввода в список (чтобы потом проверить, подряд ли они)
                        numbers.append(number)
                    if typeinput == 'pos':
                        needtext = data['pos'][index]  # ищем нужное предложение
                        text = needtext.split(' ')  # разбиваем текст, чтобы вытащить номер нужного слова
                        number = text.index(el)
                        numbers.append(number)
                    if typeinput == 'notexact':  # надо сделать начальную форму, и только потом смотреть в леммах
                        element = pymorphy_lemmas(el)
                        needtext = data['lemmas'][index]  # ищем нужное предложение
                        text = needtext.split(' ')  # разбиваем текст, чтобы вытащить номер нужного слова
                        number = text.index(element)
                        numbers.append(number)
                    if typeinput == 'wordbypos':
                        el_sp = el.split('+')
                        element_ = pymorphy_lemmas(el_sp[0])
                        needtext = data['lemmas'][index]  # ищем нужное предложение
                        needpos = data['pos'][index]
                        text = needtext.split(' ')  # разбиваем текст, чтобы вытащить номер нужного слова
                        pos = needpos.split(' ')
                        numtext = text.index(element_)  # потом доделать, чтобы было 2 условия
                        numpos = pos.index(el_sp[1])
                        if numtext == numpos:
                            numbers.append(numtext)
                n = 0
                for i in range(0, len(numbers) - 1):
                    if numbers[i] == (numbers[i + 1]) - 1:
                        n += 1
                if (n == len(numbers) - 1):
                    idxs.append(index)
            output = pd.DataFrame()
            output['id'] = data['id'].iloc[idxs]
            output['text'] = data['text'].iloc[idxs]

        return output

    inquery = search(inquery)

    html = inquery.to_html()
    with open('templates\index.html', 'w') as text_file:
        text_file.write(html)
    with open('templates\index.html', 'r') as text_file:
        text_file = text_file.read()
        return text_file
    # return render_template('greeting.html', inquery=inquery)


if __name__ == "__main__":
    app.run()
