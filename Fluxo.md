Diagrama geral do fluxo da Rosie (run)


dataset = Dataset(target_directory).get()
	__init__ do Dataset
		self.path = path
        pd.options.mode.chained_assignment = None # default='warn'
        get()
        	self.update_datasets()
            	os.makedirs(self.path, exist_ok=True)
        		ceap = c.CEAPDataset(self.path)
        			__init__ do CEAPDataset
        			ceap.fetch()
	         		ceap.convert_to_csv()
    	     		ceap.translate()
        			ceap.clean()
         			fetch(self.COMPANIES_DATASET, self.path)
         			.
         			.
         			.
         			.
         			todo