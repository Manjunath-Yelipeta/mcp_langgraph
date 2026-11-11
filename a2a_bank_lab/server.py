"""A specialist agent exposed through the official A2A SDK (protocol 1.0)."""
import json
import uvicorn
from starlette.applications import Starlette
from a2a.helpers import get_message_text, new_task_from_user_message, new_text_message, new_text_part
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill, TaskState

# Synthetic records. These are teaching rules, not fraud detection or bank policy.
PAYMENTS = {
    'TX100': {'amount': 75, 'currency': 'AED', 'recognized_device': True},
    'TX200': {'amount': 12000, 'currency': 'AED', 'recognized_device': False},
}

class PaymentReviewExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue):
        task = context.current_task or new_task_from_user_message(context.message)
        if context.current_task is None:
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.context_id)
        await updater.update_status(
            TaskState.TASK_STATE_WORKING, new_text_message('Checking synthetic payment records'))
        payment_id = get_message_text(context.message).strip().upper()
        payment = PAYMENTS.get(payment_id)
        if payment is None:
            report = {'payment_id': payment_id, 'outcome': 'not_found',
                      'reason': 'Try TX100 or TX200. No payment was changed.'}
        else:
            review = payment['amount'] >= 10000 or not payment['recognized_device']
            report = {'payment_id': payment_id, **payment,
                      'outcome': 'manual_review' if review else 'no_demo_risk_flags',
                      'reason': 'Large amount or unfamiliar device' if review else 'Neither demo rule matched',
                      'action_taken': 'none; advisory report only'}
        await updater.add_artifact(
            parts=[new_text_part(text=json.dumps(report, indent=2), media_type='text/plain')],
            name='payment-review.json')
        await updater.update_status(TaskState.TASK_STATE_COMPLETED,
                                    new_text_message('Review report ready'))

    async def cancel(self, context, event_queue):
        raise NotImplementedError('Cancellation is outside this first lab')

card = AgentCard(
    name='Payment Review Specialist', description='Reviews synthetic disputed payments',
    version='1.0.0', default_input_modes=['text/plain'], default_output_modes=['text/plain'],
    capabilities=AgentCapabilities(streaming=True),
    supported_interfaces=[AgentInterface(protocol_binding='JSONRPC',
        url='http://127.0.0.1:9999/', protocol_version='1.0')],
    skills=[AgentSkill(id='review_payment', name='Review payment',
        description='Send TX100 or TX200 to receive an advisory review report',
        tags=['banking', 'payments'], examples=['TX100', 'TX200'])])
handler = DefaultRequestHandler(agent_executor=PaymentReviewExecutor(),
    task_store=InMemoryTaskStore(), agent_card=card)
app = Starlette(routes=[*create_agent_card_routes(card), *create_jsonrpc_routes(handler, '/')])

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=9999)
