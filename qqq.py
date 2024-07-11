q = 'select * from "кластер 1"'

tablitsa = q.split()
# найти индекс элемента 'from'
from_index = tablitsa.index('from')

# объединить части, начиная с элемента 'from'
from_clause = ' '.join(tablitsa[from_index:])
tablitsa = from_clause

print('tablitsa: ', tablitsa)

#dlina = execute_query(f"SELECT COUNT(*) {tablitsa} WHERE object = '{param[0]}'")
