# Generates sentences with context for all different settings

for before in $(seq 0 10); do 
	for after in $(seq 0 10); do 
		echo "before=$before after=$after"
		../bin/json2text.py -s en -t de --max-sents $total --sents-before $before --separator ' <eos>' > contrapro-$before-$after.en-de.tsv
	done
done
