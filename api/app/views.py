from aiohttp.hdrs import METH_POST
from aiohttp.web_exceptions import HTTPFound
from aiohttp.web_response import Response
from pydantic import BaseModel, ValidationError, constr


class FormModel(BaseModel):
    username: constr(max_length=40)
    message: str


async def process_form(request):
    data = dict(await request.post())
    try:
        m = FormModel(**data)
    except ValidationError as exc:
        return exc.errors()

    await request.app['pg'].execute('insert into messages (username, message) values ($1, $2)', m.username, m.message)
    raise HTTPFound(request.app.router['messages'].url_for())


async def messages(request):
    if request.method == METH_POST:
        # the 302 redirect is processed as an exception, so if this coroutine returns there's a form error
        form_errors = await process_form(request)
    else:
        form_errors = None

    return {'title': 'Message board', 'form_errors': form_errors, 'username': 'kek'}


async def message_data(request):
    """
    As an example of aiohttp providing a non-html response, we load the actual messages for the "messages" view above
    via ajax using this endpoint to get data. see static/message_display.js for details of rendering.
    """
    json_str = await request.app['pg'].fetchval(
        """
        select coalesce(array_to_json(array_agg(row_to_json(t))), '[]')
        from (
          select username, timestamp, message
          from messages
          order by timestamp desc
        ) t
        """
    )
    return Response(text=json_str, content_type='application/json')
