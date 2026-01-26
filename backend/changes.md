## pytest
In the backend/ folder, tests are all in the test/ folder but to properly run pytest you have to do `pytest test/ -v`.

To run a specific test you do `python tests/test_student_socketio.py::test_no_uuid -v` for example

In socketio_client pytest fixture, the client is automatically connected as test_client(app) is called. but because of `user_id = auth.get("uuid")`, it would be necessary in a test scenario for specify the auth headers when a student is connecting with an existing uuid like when a student refreshes their page. So then in socketio_client fixture the client is automatically disconnected then manually connected in a test. But in some tests its not fine to have the client automatically disconnected so `disconnect=False` must be specified for such tests.

Why do we have to specify the test_client in our pytests? its so we can allow sessions to able to SET/GET. socketio_client cannot set session variables unless you directly interact with `.flask_test_client` to do a session transaction to read/write the session variable (see set_session and get_session). Since socketio test clients are automatically connection as they're intialised, we have to manually disconnect the client before we can interact with the session. Instead, we can pass the un-initialised client before creating the socketio client. Technically you can also pass the socketio client directly to set_session/get_session by design but that would require you to connect (auto) --> disconnect --> connect (again ugh).

When the server emits something back to the client, you can access the payloads via get_received(), get_last_recieved just gets the last sent payload.


## server.py
~~Removed join_room(user_id) because its useless, whatever you emit is only relative to the current session connected to that room unless you specify `broadcast=True` (although session IDs change every time you refresh the session variables do not clear out). also i really hate the concept of joining multiple rooms at the same time~~

^ I CHANGED MY MIND, i think that was actually necessary to broadcast to all sessions of the same user, which is better than the O(N) loop i did in my implementation, having join_room(user_id) turns it to O(1).

I flattened the data structure for student details in _join_tutorial and /details route so its cleaner, also these session variables are popped to avoid redundancy since these details are expected to be asked once.
