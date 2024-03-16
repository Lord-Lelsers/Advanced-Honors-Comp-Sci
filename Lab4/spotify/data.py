import pandas as pd
import numpy as np

np.set_printoptions(precision=3, suppress=True)

DATA_PATH = 'data/data.csv'
POPULARITY_COLUMN_COUNT = 10


def load_data():
	data = pd.read_csv(DATA_PATH)
	print(data.head())
	print(data.info())

	data_features = data.copy()

	pop_to_column = lambda x: int(x / POPULARITY_COLUMN_COUNT) + 1
	data_features['popularity'] = data_features['popularity'].apply(pop_to_column)

	data_labels = data_features.pop('popularity') # target

	data_features.pop('artists')
	data_features.pop('explicit')
	data_features.pop('id')
	data_features.pop('mode')
	data_features.pop('name')
	data_features.pop('release_date')


	print(data_features.head())
	print(data_features.info())

	data_features = np.asarray(data_features).astype(np.float32)
	print(data_features)

	return data_features, data_labels