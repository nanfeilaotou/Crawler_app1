import pandas as pd

docA = 'The cat sat on my bed'
docB = 'The dog sat on my knees'
bowA = docA.split(' ')
bowB = docB.split(' ')
# 构建词库
wordSet = set(bowA).union(set(bowB))
# 2. 进行词数统计
# 用一个统计字典来保存词出现的词数
wordDictA = dict.fromkeys(wordSet, 0)  # 每个字典的值从0开始统计，最后不出现的次数依然是0
wordDictB = dict.fromkeys(wordSet, 0)
# 遍历文档，统计词数
for word in bowA:
    wordDictA[word] += 1
for word in bowB:
    wordDictB[word] += 1
print(pd.DataFrame([wordDictA]))  # 看一下结果 pd.DataFrame以表格的形式显示出来
print(pd.DataFrame([wordDictB]))


# 3. 计算词频TF
def computeTF(wordDict, bow):  # wordDict: 统计次数的字典， bow: 每个文档所有的词数
    # 用一个字典对象记录tf，把所有的词对应在bow文档里的tf都算出来
    tfDict = {}
    nbowCount = len(bow)  # 计算所有的词
    for word, count in wordDict.items():
        tfDict[word] = count / nbowCount  # 计算词频，出现词数/总词数
    return tfDict


# 测试
tfA = computeTF(wordDictA, bowA)
tfB = computeTF(wordDictB, bowB)
print(pd.DataFrame(list(tfA.items())))
print(pd.DataFrame([tfB]))


# 4. 计算逆文档频率IDF
def computeIDF(wordDictList):  # wordDict:文档的每个单词都有（key），出现的词数也有（value）
    # 用一个字典对象保存IDF结果，每个词作为key，初始值为0
    idfDict = dict.fromkeys(wordDictList[0], 0)
    # 总文档数量N
    N = len(wordDictList)
    import math
    for wordDict in wordDictList:
        # 遍历字典中的每个词汇,统计Ni Ni：文档包含词语的数量
        for word, count in wordDict.items():
            if count > 0:
                # 先把Ni增加1，存入到idfDict
                idfDict[word] += 1


# 已经得到所有词汇i对应的Ni, 现在根据公式把它替换为idf值
        for word, ni in idfDict.items():
            idfDict[word] = math.log10((N + 1) / (ni + 1))
        return idfDict

# 测试
idfs = computeIDF([wordDictA, wordDictB])
print(pd.DataFrame(list(idfs.items())))
# 5. 计算TD-IDF
def computeTFIDF(tf, idfs):
    tfidf = {}
    for word, tfval in tf.items():
        tfidf[word] = tfval * idfs[word]
    return tfidf


tfidfA = computeTFIDF(tfA, idfs)
tfidfB = computeTFIDF(tfB, idfs)

print(pd.DataFrame([tfidfA, tfidfB]))
print(pd.DataFrame(list(tfidfA.items()), list(tfidfB.items())))