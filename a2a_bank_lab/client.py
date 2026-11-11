"""A minimal bank support agent: discover, delegate, inspect the response."""
import argparse
import asyncio
import httpx
from google.protobuf.json_format import MessageToJson
from a2a.client import A2ACardResolver, ClientConfig, create_client
from a2a.helpers import new_text_message
from a2a.types import Role, SendMessageRequest

async def main(payment_id, stream):
    async with httpx.AsyncClient() as http:
        card = await A2ACardResolver(httpx_client=http,
            base_url='http://127.0.0.1:9999').get_agent_card()
    print(f'1. Discovered: {card.name}')
    print(f'2. Skill: {card.skills[0].name}')
    client = await create_client(agent=card, client_config=ClientConfig(streaming=stream))
    try:
        print(f'3. Delegating {payment_id}; streaming={stream}')
        request = SendMessageRequest(message=new_text_message(payment_id, role=Role.ROLE_USER))
        async for event in client.send_message(request):
            print(MessageToJson(event))
    finally:
        await client.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('payment_id', nargs='?', default='TX200')
    parser.add_argument('--stream', action='store_true')
    args = parser.parse_args()
    asyncio.run(main(args.payment_id, args.stream))
