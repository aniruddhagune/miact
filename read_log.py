with open('out_gsmarena.txt', 'r', encoding='utf-16-le') as f:
    print(f.read().encode('utf-8').decode('utf-8'))
