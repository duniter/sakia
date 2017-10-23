#!/bin/bash

wget https://duniter.org/en/files/licence_g1.txt
sed "s/:date.*//g" -i licence_g1.txt
sed "s/:modified.*//g" -i licence_g1.txt
pandoc -s licence_g1.txt -o src/sakia/g1_licence.html
rm licence_g1.txt
