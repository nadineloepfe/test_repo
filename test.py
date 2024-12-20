import os
import sys
from dotenv import load_dotenv
from hedera_sdk_python.client.network import Network
from hedera_sdk_python.client.client import Client
from hedera_sdk_python.account.account_id import AccountId
from hedera_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hedera_sdk_python.crypto.private_key import PrivateKey
from hedera_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hedera_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hedera_sdk_python.transaction.transfer_transaction import TransferTransaction
from hedera_sdk_python.response_code import ResponseCode
from hedera_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hedera_sdk_python.consensus.topic_message_submit_transaction import TopicMessageSubmitTransaction

load_dotenv()

def load_operator_credentials():
    """Load operator credentials from environment variables."""
    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
        operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
    except Exception as e:
        print(f"Error parsing operator credentials: {e}")
        sys.exit(1)

    return operator_id, operator_key

def create_new_account(client, initial_balance=100000000):
    """Creates a new account on the Hedera network and returns the account ID and private key."""
    new_account_private_key = PrivateKey.generate()
    new_account_public_key = new_account_private_key.public_key()

    transaction = (
        AccountCreateTransaction()
        .set_key(new_account_public_key)
        .set_initial_balance(initial_balance)  # initial balance in tinybars
        .set_account_memo("Recipient Account")
        .freeze_with(client)
    )
    transaction.sign(client.operator_private_key)

    try:
        receipt = transaction.execute(client)
        new_account_id = receipt.accountId

        if new_account_id is not None:
            print(f"Account creation successful. New Account ID: {new_account_id}")
            print(f"New Account Private Key: {new_account_private_key.to_string()}")
            print(f"New Account Public Key: {new_account_public_key.to_string()}")
        else:
            raise Exception("AccountID not found in receipt. Account may not have been created.")
    except Exception as e:
        print(f"Account creation failed: {str(e)}")
        sys.exit(1)

    return new_account_id, new_account_private_key

def create_token(client, operator_id):
    """Create a new token and return its TokenId instance."""

    transaction = (
        TokenCreateTransaction()
        .set_token_name("ExampleToken")
        .set_token_symbol("EXT")
        .set_decimals(2)
        .set_initial_supply(1000)
        .set_treasury_account_id(operator_id)
        .freeze_with(client)
    )

    transaction.sign(client.operator_private_key)

    try:
        receipt = transaction.execute(client)
    except Exception as e:
        print(f"Token creation failed: {str(e)}")
        sys.exit(1)

    if not receipt.tokenId:
        print("Token creation failed: Token ID not returned in receipt.")
        sys.exit(1)

    token_id = receipt.tokenId
    print(f"Token creation successful. Token ID: {token_id}")

    return token_id

def associate_token(client, recipient_id, recipient_private_key, token_id):
    """Associate the specified token with the recipient account."""
    transaction = (
        TokenAssociateTransaction()
        .set_account_id(recipient_id)
        .add_token_id(token_id)
        .freeze_with(client)
    )
    transaction.sign(client.operator_private_key) # sign with operator's key (payer)
    transaction.sign(recipient_private_key) # sign with newly created account's key (recipient)

    try:
        receipt = transaction.execute(client)
        if receipt.status != ResponseCode.SUCCESS:
            status_message = ResponseCode.get_name(receipt.status)
            raise Exception(f"Token association failed with status: {status_message}")
        print("Token association successful.")
    except Exception as e:
        print(f"Token association failed: {str(e)}")
        sys.exit(1)

def transfer_token(client, recipient_id, token_id):
    """Transfer the specified token to the recipient account."""
    transaction = (
        TransferTransaction()
        .add_token_transfer(token_id, client.operator_account_id, -1)
        .add_token_transfer(token_id, recipient_id, 1)
        .freeze_with(client)
    )
    transaction.sign(client.operator_private_key)

    try:
        receipt = transaction.execute(client)
        if receipt.status != ResponseCode.SUCCESS:
            status_message = ResponseCode.get_name(receipt.status)
            raise Exception(f"Token transfer failed with status: {status_message}")
        print("Token transfer successful.")
    except Exception as e:
        print(f"Token transfer failed: {str(e)}")
        sys.exit(1)

def create_topic(client):
    key = client.operator_private_key
    transaction = (
        TopicCreateTransaction(
            memo="Python SDK created topic",
            admin_key=key.public_key())
        .freeze_with(client)
        .sign(key)
    )
    try:
        receipt = transaction.execute(client)
    except Exception as e:
        print(f"Topic creation failed: {str(e)}")
        sys.exit(1)

    if not receipt.topicId:
        print("Topic creation failed: Topic ID not returned in receipt.")
        sys.exit(1)

    topic_id = receipt.topicId
    print(f"Topic creation successful. Topic ID: {topic_id}")

    return topic_id

def submit_message(client, topic_id):
    transaction = (
        TopicMessageSubmitTransaction(topic_id=topic_id, message="Hello, Python SDK!")
        .freeze_with(client)
        .sign(client.operator_private_key)
    )
    try:
        receipt = transaction.execute(client)
    except Exception as e:
        print(f"Message submission failed: {str(e)}")
        sys.exit(1)

    if receipt.status != ResponseCode.SUCCESS:
        status_message = ResponseCode.get_name(receipt.status)
        raise Exception(f"Message submission failed with status: {status_message}")

    print("Message submitted successfully.")

def update_topic(client):
    key = client.operator_private_key
    transaction = (
        TopicCreateTransaction(
            memo="Python SDK updated topic")
        .freeze_with(client)
        .sign(key)
    )
    try:
        receipt = transaction.execute(client)
    except Exception as e:
        print(f"Topic update failed: {str(e)}")
        sys.exit(1)

    if receipt.status != ResponseCode.SUCCESS:
        status_message = ResponseCode.get_name(receipt.status)
        raise Exception(f"Topic update failed with status: {status_message}")

    print("Topic updated successfully.")

def main():
    operator_id, operator_key = load_operator_credentials()

    network_type = os.getenv('NETWORK')
    network = Network(network=network_type)

    client = Client(network)
    client.set_operator(operator_id, operator_key)

    recipient_id, recipient_private_key = create_new_account(client)
    token_id = create_token(client, operator_id)
    associate_token(client, recipient_id, recipient_private_key, token_id)
    transfer_token(client, recipient_id, token_id)

    topic_id = create_topic(client)
    submit_message(client, topic_id)
    update_topic(client)

if __name__ == "__main__":
    main()
