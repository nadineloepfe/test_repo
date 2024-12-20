import os
import sys
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from hedera_sdk_python.client.client import Client
from hedera_sdk_python.account.account_id import AccountId
from hedera_sdk_python.consensus.topic_id import TopicId
from hedera_sdk_python.crypto.private_key import PrivateKey
from hedera_sdk_python.client.network import Network
from hedera_sdk_python.consensus.topic_update_transaction import TopicUpdateTransaction

load_dotenv()

def update_topic():
    network = Network(network='testnet')
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
    admin_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))

    client.set_operator(operator_id, operator_key)

    new_topic_id = TopicId.from_string(os.getenv('TOPIC_ID'))

    transaction = (
        TopicUpdateTransaction(topic_id=new_topic_id, submit_key=admin_key.public_key())
        .freeze_with(client)
        .sign(operator_key)
    )
    transaction.sign(admin_key)

    try:
        receipt = transaction.execute(client)
        if receipt and receipt.topicId:
            print(f"Topic updated with ID: {receipt.topicId}")
        else:
            print("Topic update failed: Topic ID not returned in receipt.")
            sys.exit(1)
    except Exception as e:
        print(f"Topic update failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    update_topic()
