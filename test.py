# # import huggingface_hub
# # from langchain_community.document_loaders.mongodb import MongodbLoader
# # from langchain_text_splitters import RecursiveCharacterTextSplitter
# # from langchain_community.vectorstores.mongodb_atlas import MongoDBAtlasVectorSearch
# # from Controller.bookController import book_database
# # from langchain_huggingface.embeddings import HuggingFaceEndpointEmbeddings
# #
# #
# # db_vector_search = MongoDBAtlasVectorSearch(
# #     collection= book_database
# # )
# #
# # loader = MongodbLoader(
# #     connection_string="mongodb+srv://admin:nfPOPZZrWWKKim5D@haiimphuong.pehm7k8.mongodb.net/",
# #     db_name="BooksManagement",
# #     collection_name="Book",
# #
# # )
# #
# # docs = loader.load()
# #
# # text_splitter = RecursiveCharacterTextSplitter(
# #     add_start_index=True,
# # )
# #
# # all_split_docs = text_splitter.split_documents(docs)
# #
# # print(len(all_split_docs))
# #
# # # #
# # # # len_list = []
# # # # for doc in docs:
# # # #     len_list.append(len(str(doc)))
# # # #
# # # # for i in range(len(len_list)):
# # # #     if len_list[i] == max(len_list):
# # # #         print(str(docs[i]))
# # # #         print(len(str(docs[i])))
# # #
# # # print(docs[0].dict())
#
# import transformers
# embed_model = transformers.AutoModel.from_pretrained("BAAI/bge-base-en-v1.5")

from Controller.bookController import book_database, BookController

async def get_books():
    books = await BookController.get_books(get_all=True)
    print(len(books))
