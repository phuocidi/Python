import pickle
from sys import argv

if not argv[1]:
    print('Nah')
    exit()
        
fileClients = argv[1]
print(fileClients)
data = pickle.load(open(fileClients))
print (data['client.059'])

