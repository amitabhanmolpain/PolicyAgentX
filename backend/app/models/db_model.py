from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["policyagentx"]

policy_collection = db["policy_results"]