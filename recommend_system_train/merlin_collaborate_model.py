from metaflow import FlowSpec, step, batch, Parameter, current, retry
from custom_decorators import magicdir
import os
import json
from datetime import datetime
from pyarrow import Table

class End2EndRecommenderFlow(FlowSpec):

    ### MERLIN PARAMETERS ###

    MODEL_FOLDER = Parameter(
        name='model_folder',
        help='Folder to store the model from Merlin, between steps',
        default='merlin_model'
    )
    DATA_FOLDER = Parameter(
        name='data_folder',
        help='Folder to store the data and model from Merlin, between steps',
        default='/content'
    )

    ### DATA PARAMETERS ###

    ROW_SAMPLING = Parameter(
        name='row_sampling',
        help='Row sampling: if 0, NO sampling is applied. Needs to be an int between 1 and 100',
        default='1'
    )


    TRAINING_END_DATE = Parameter(
        name='training_end_date',
        help='Data up until this date is used for training, format yyyy-mm-dd',
        default='2020-09-08'
    )

    VALIDATION_END_DATE = Parameter(
        name='validation_end_date',
        help='Data up after training end and until this date is used for validation, format yyyy-mm-dd',
        default='2020-09-15'
    )

    ### TRAINING PARAMETERS ###

    VALIDATION_METRIC = Parameter(
        name='validation_metric',
        help='Merlin metric to use for picking the best set of hyperparameter',
        default='recall_at_10'
    )

    N_EPOCHS = Parameter(
        name='n_epoch',
        help='Number of epochs to train the Merlin model',
        default='1' # default to 1 for quick testing
    )

    ### SERVING PARAMETERS ###

    SAVE_TO_CACHE = Parameter(
        name='save_to_cache',
        help='Enable / disable (1/0) saving the best predictions to a key value store',
        default='0' # default to 0 - NO CACHING
    )

    DYNAMO_TABLE = Parameter(
        name='dynamo_table',
        help='Name of dynamo db table to store the pre-computed recs. Default is same as in the serverless application',
        default='userItemTable'
    )

    TOP_K = Parameter(
        name='top_k',
        help='Number of products to recommend for a giver shopper',
        default='10'
    )

    @step
    def start(self):
        """
        Start-up: check everything works or fail fast!
        """
        # print out some debug info
        print("flow name: %s" % current.flow_name)
        

        self.next(self.process_data)
    
    @step
    def process_data(self):
      import pandas as pd

      _df = pd.read_csv(
          r'/content/Books Data with Category Language and Summary/Preprocessed_data.csv',
          on_bad_lines='skip',
          sep=",")
      # show the df
      print(_df.head())
      print(_df.dtypes)
      # print the lenght
      print(len(_df))
      # dump to parquet (better than csv for duckdb)
      _df.to_parquet('Preprocessed_data')
      self.next(self.get_dataset)

    @step
    def get_dataset(self):
        """
        Get the data in the right shape using duckDb, after the dbt transformation
        """
        from pyarrow import Table as pt
        from sklearn.model_selection import train_test_split
        import pandas as pd
        import duckdb
        # check if we need to sample - this is useful to iterate on the code with a real setup
        # without reading in too much data...
        _sampling = int(100)
        sampling_expression = '' if _sampling == 0 else 'USING SAMPLE {} PERCENT (bernoulli)'.format(_sampling)
        # thanks to our dbt preparation, the ML models can read in directly the data without additional logic
        query = """
            SELECT
                user_id,
                location,
                age,
                isbn,
                rating,
            book_title, book_author, year_of_publication, publisher,
            img_s, Summary, Language, Category, city
            FROM
                read_parquet('/content/Preprocessed_data')
                {}
            ORDER BY
                year_of_publication ASC
        """.format(sampling_expression)
        print("Fetching rows with query: \n {} \n\nIt may take a while...\n".format(query))
       # fetch raw dataset
        con = duckdb.connect(database=':memory:')
        con.execute(query)
        dataset = con.fetchall()
        # convert the COLS to lower case (Keras does complain downstream otherwise)
        cols = [c[0].lower() for c in con.description]
        dataset = [{ k: v for k, v in zip(cols, row) } for row in dataset]
        # debug
        print("Example row", dataset[0])
        self.user_id_2_meta = { str(r['user_id']): r for r in dataset }
  

        # Convert to Pandas DataFrame for easier manipulation
        df = pd.DataFrame(dataset)  

        # Split into train and test sets (80%/20%)
        train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)

        # Further split train set into train and validation (80%/20%)
        train_df, valid_df = train_test_split(train_df, test_size=0.25, random_state=42)

        # Convert back to PyArrow Table
        train_dataset = pt.from_pandas(train_df)
        validation_dataset = pt.from_pandas(valid_df)
        test_dataset = pt.from_pandas(test_df)

        print("# {:,} events in the training set, {:,} for validation, {:,} for test".format(
            len(train_dataset),
            len(validation_dataset),
            len(test_dataset)
        ))
        # store and version datasets as a map label -> datasets, for consist processing later on
        self.label_to_dataset = {
            'train': train_dataset,
            'valid': validation_dataset,
            'test': test_dataset
        }

        # go to the next step for NV tabular data
        self.next(self.build_workflow)
    

    def read_to_dataframe(self,
        dataset: Table,
        label: str # follows naming convention train,valid,test
        ):
        
        import pandas as pd
        from pyarrow.parquet import write_table
        write_table(dataset, '{}.parquet'.format(label))
        return pd.read_parquet('{}.parquet'.format(label))


    def get_nvt_workflow(self):
        from pyarrow import Table
        import nvtabular.ops as ops
        import numpy as np
        import nvtabular as nvt

        user_id = ["user_id"] >> ops.Categorify() >> ops.AddMetadata(tags=["user_id", "user"])
        user_features = [
            "location"] >> ops.Categorify() >> ops.AddMetadata(tags=["user"])

        age_boundaries = list(np.arange(0,100,5))
        user_age = ["age"] >> ops.FillMissing(0) >> ops.Bucketize(age_boundaries) >> ops.Categorify() >> ops.AddMetadata(tags=["user"])
        user_features = user_features + user_age

        rating = (
            ["rating"]
        )



        context_features = (
            rating >> ops.Categorify() >>  ops.AddMetadata(tags=["user"])
        )

        item_id = ["isbn"] >> ops.Categorify() >> ops.AddMetadata(tags=["item_id", "item"])
        item_features = ["book_title",
                "book_author",
                "year_of_publication",
                "publisher",
                "city"] >> ops.Categorify() >>  ops.AddMetadata(tags=["item"])



        outputs = user_id + user_features + context_features + item_id + item_features

        workflow = nvt.Workflow(outputs)

        return workflow
    
    # NOTE: we use the magicdir package (https://github.com/outerbounds/metaflow_magicdir)
    #to simplify moving the parquet files that Merlin needs / consumes across steps
    @magicdir
    @step
    def build_workflow(self):
        """
        Use NVTabular to transform the original data into the final dataframes for training,
        validation, testing.
        """
        import pandas as pd
        import nvtabular as nvt # pylint: disable=import-error
        import itertools
        # read dataset into frames
        label_to_df = {}
        for label, dataset in self.label_to_dataset.items():
            label_to_df[label] = self.read_to_dataframe(dataset, label)
        full_dataset = nvt.Dataset(pd.concat(list(label_to_df.values())))
        # get the workflow and fit the dataset
        workflow = self.get_nvt_workflow()
        workflow.fit(full_dataset)
        self.label_to_melin_dataset = {}
        for label, _df in label_to_df.items():
            cnt_dataset = nvt.Dataset(_df)
            self.label_to_melin_dataset[label] = cnt_dataset
            workflow.transform(cnt_dataset).to_parquet(output_path="merlin/{}/".format(label))
        # store the mapping Merlin ID -> article_id and Merlin ID -> customer_id
        self.user_unique_ids = list(pd.read_parquet('categories/unique.user_id.parquet')['user_id'])
        self.items_unique_ids = list(pd.read_parquet('categories/unique.isbn.parquet')['isbn'])
        self.id_2_user_id = { idx:_ for idx, _ in enumerate(self.user_unique_ids) }
        self.id_2_item_id = { idx:_ for idx, _ in enumerate(self.items_unique_ids) }
  
        self.next(self.train_model)


    @retry
    @magicdir
    @step
    def train_model(self):
        """
        Train models in parallel and store artifacts and validation KPIs for downstream consumption.
        """
        import hashlib
        import merlin.models.tf as mm # pylint: disable=import-error
        from merlin.io.dataset import Dataset # pylint: disable=import-error
        from merlin.schema.tags import Tags # pylint: disable=import-error
        from merlin.models.utils.dataset import unique_rows_by_features 
        import tensorflow as tf # pylint: disable=import-error
        # this is the CURRENT hyper param JSON in the fan-out
        # each copy of this step in the parallelization will have its own value
        train = Dataset('merlin/train/*.parquet')
        valid = Dataset('merlin/valid/*.parquet')
        print("Train dataset shape: {}, Validation: {}".format(
            train.to_ddf().compute().shape,
            valid.to_ddf().compute().shape
            ))
        # train the model and evaluate it on validation set
        user_schema = train.schema.select_by_tag(Tags.USER) # MERLIN WARNING
        user_inputs = mm.InputBlockV2(user_schema)
        query = mm.Encoder(user_inputs, mm.MLPBlock([128, 64]))
        item_schema = train.schema.select_by_tag(Tags.ITEM)
        item_inputs = mm.InputBlockV2(item_schema,)
        candidate = mm.Encoder(item_inputs, mm.MLPBlock([128, 64]))
        model = mm.TwoTowerModelV2(query, candidate)
        opt = tf.keras.optimizers.Adagrad(learning_rate=0.04)
        model.compile(
            optimizer=opt, 
            run_eagerly=False, 
            metrics=[mm.RecallAt(int(10)), mm.NDCGAt(int(10))],)
        model.fit(
            train, 
            validation_data=valid, 
            batch_size=4096, 
            epochs=int(10))
        self.metrics = model.evaluate(valid, batch_size=1024, return_dict=True)
        print("\n\n====> Eval results: {}\n\n".format(self.metrics))
        self.hyper_string="150204"
        # save the model
        model_hash = str(hashlib.md5(self.hyper_string.encode('utf-8')).hexdigest())
        self.model_path = 'merlin/model{}/'.format(model_hash)
        model.save(self.model_path)
        print(f"Model saved to {self.model_path}!")
        # next, for the best model do more testing  
        # saving user embedding, user features and item embedding, item features
        query_tower = model.query_encoder
        query_tower.save(os.path.join(self.DATA_FOLDER, "query_tower"))
        user_features = unique_rows_by_features(train, Tags.USER, Tags.USER_ID).to_ddf().compute().reset_index(drop=True)

        user_features.head()
        user_features.to_parquet(os.path.join(self.DATA_FOLDER, "user_features.parquet"))

        queries = model.query_embeddings(Dataset(user_features, schema=user_schema), 
                                 batch_size=1024, index=Tags.USER_ID)
        query_embs_df = queries.compute(scheduler="synchronous").reset_index()

        query_embs_df.head()

        item_features = (
    unique_rows_by_features(train, Tags.ITEM, Tags.ITEM_ID).to_ddf().compute().reset_index(drop=True)
)
        item_features.head()
        # save to disk
        item_features.to_parquet(os.path.join(self.DATA_FOLDER, "item_features.parquet"))

        item_embs = model.candidate_embeddings(Dataset(item_features, schema=item_schema), 
                                       batch_size=1024, index=Tags.ITEM_ID)
        item_embs_df = item_embs.compute(scheduler="synchronous")
        item_embs_df.head()
        item_embs_df.to_parquet(os.path.join(self.DATA_FOLDER, "item_embeddings.parquet"))

        self.next(self.end)

    
    def get_items_topk_recommender_model(
        self,
        train_dataset, 
        model, 
        k: int
    ):
        from merlin.models.utils.dataset import unique_rows_by_features # pylint: disable=import-error
        from merlin.schema.tags import Tags # pylint: disable=import-error
        candidate_features = unique_rows_by_features(train_dataset, Tags.ITEM, Tags.ITEM_ID)
        topk_model = model.to_top_k_encoder(candidate_features, k=k, batch_size=128)
        topk_model.compile(run_eagerly=False)

        return topk_model

    def load_merlin_model(
        self,
        dataset,
        path
    ):
        import tensorflow as tf # pylint: disable=import-error
        import merlin.models.tf as mm # pylint: disable=import-error
        loaded_model = tf.keras.models.load_model(path, compile=False)
        # this is necessary when re-loading the model, before building the top K
        _ = loaded_model(mm.sample_batch(dataset, batch_size=128, include_targets=False))
        # debug
        print("Model re-loaded!")

        return loaded_model

    # @retry
    # @magicdir
    # @step
    def model_testing(self):
        """
        Test the generalization abilities of the best model through the held-out set...
        and RecList Beta (Forthcoming!)
        """
        from merlin.io.dataset import Dataset # pylint: disable=import-error
        import merlin.models.tf as mm # pylint: disable=import-error
        from merlin.schema import Tags # pylint: disable=import-error
        # loading back datasets and the model for final testing
        test = Dataset('merlin/test/*.parquet')
        train = Dataset('merlin/train/*.parquet')
        loaded_model = self.load_merlin_model(train, self.model_path)
        topk_rec_model = self.get_items_topk_recommender_model(test, loaded_model, k=int(10))
        # extract the target item id from the inputs
        test_loader = mm.Loader(test, batch_size=1024, transform=mm.ToTarget(test.schema, Tags.ITEM_ID))
        self.test_metrics = topk_rec_model.evaluate(test_loader, batch_size=1024, return_dict=True)
        print("\n\n====> Test results: {}\n\n".format(self.test_metrics))        
        # calculate recommendations 
        topk_rec_model = self.get_items_topk_recommender_model(train, loaded_model, k=int(10))
        self.best_predictions = self.get_recommendations(test, topk_rec_model)
        # cache predictions
        self.next(self.cache_predictions)
            
    def get_recommendations(
        self,
        test,
        topk_rec_model 
    ):
        """
        Run predictions on a target dataset of shoppers (in this case, the testing dataset) 
        and store the predictions for the cache downstream.
        """
        import merlin.models.tf as mm # pylint: disable=import-error
        # export ONLY the users in the test set to simulate the set of shoppers we need to recommend items to
        test_dataset = mm.Loader(test, batch_size=1024, shuffle=False)
        # predict returns a tuple with two elements, scores and product IDs: we get the IDs only
        self.raw_predictions = topk_rec_model.predict(test_dataset)[1]
        n_rows = self.raw_predictions.shape[0]
        self.target_shoppers = test_dataset.data.to_ddf().compute()['user_id']
        print("Inspect the shopper object for debugging...{}".format(type(self.target_shoppers)))
        # check we have as many predictions as we have shoppers in the test set
        assert n_rows == len(self.target_shoppers)
        # map predictions to a final dictionary, with the actual H and M IDs for users and products
        self.h_m_shoppers = [str(self.id_2_user_id[_]) for _ in self.target_shoppers.to_numpy().tolist()]
        print("Example target shoppers: ", self.h_m_shoppers[:3])
        self.target_items = test_dataset.data.to_ddf().compute()['isbn']
        print("Example target items: ", self.target_items[:3])
        predictions = self.serialize_predictions(
            self.h_m_shoppers,
            self.id_2_item_id,
            self.raw_predictions,
            self.target_items,
            n_rows
        )
        print("Example target predictions", predictions[self.h_m_shoppers[0]])
        # debug, if rows > len(predictions), same user appears at least twice in test set
        print(n_rows, len(predictions))
        
        return predictions

    def serialize_predictions(
        self,
        h_m_shoppers,
        id_2_item_id,
        raw_predictions,
        target_items,
        n_rows
    ):
        """
        Convert raw predictions to a dictionary user -> items for easy re-use 
        later in the pipeline (e.g. dump the predicted items to a cache!)
        """
        sku_convert = lambda x: [str(id_2_item_id[_]) for _ in x]
        predictions = {}
        for _ in range(n_rows):
            cnt_user = h_m_shoppers[_]
            cnt_raw_preds = raw_predictions[_].tolist()
            cnt_target = target_items[_]
            # don't overwite if we already have a prediction for this user
            if cnt_user not in predictions:
                predictions[cnt_user] = {
                    'items': sku_convert(cnt_raw_preds),
                    'target': sku_convert([cnt_target])[0]
                }

        return predictions

    @step
    def cache_predictions(self):
        """
        Use DynamoDb as a cache and a Lambda (in the serverless folder, check the README)
        to serve pre-computed predictions in a PaaS/FaaS manner.

        Note (see train_model above): we are just storing the predictions for the winning model, as 
        computed in the training step.

        """

        # skip the deployment if not needed
        if not bool(int(self.SAVE_TO_CACHE)):
            print("Skipping deployment")
            print(self.SAVE_TO_CACHE)
        else:
            print("Caching predictions in DynamoDB")
            import boto3
            dynamodb = boto3.resource('dynamodb')
            table = dynamodb.Table(self.DYNAMO_TABLE)
            # upload some static items as a test
            data = [{'userId': user, 'recs': json.dumps(recs) } for user, recs in self.best_predictions.items()] 
            # finally add test user
            data.append({'userId': 'no_user', 'recs': json.dumps(['test_rec_{}'.format(_) for _ in range(int(self.TOP_K))])})
            # loop over predictions and store them in the table
            with table.batch_writer() as writer:
                for item in data:
                    writer.put_item(Item=item)
            print("Predictions are all cached in DynamoDB")

        self.next(self.end)

    @step
    def end(self):
        """
        Just say bye!
        """
        print("All done\n\nSee you, recSys cowboy\n")
        return


if __name__ == '__main__':
    End2EndRecommenderFlow()