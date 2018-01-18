import nltk
import string

def preprocess(line):
	if ":" in line:
		line = line.split(':')[0]
	while line[0] in string.punctuation:
		line = line[1:]
	line = line.replace("\,", ",")
	return line[:-1]

tags = "../moocs_tags"
listOfPhrases = open(tags, "r")
for line in listOfPhrases:
	line = preprocess(line)
	temp = line.split()
	if len(temp) > 1:
		text = nltk.word_tokenize(line)
		x = nltk.pos_tag(text)
		print (x)