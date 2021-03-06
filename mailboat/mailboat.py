# Copyright (C) 2021 The Mailboat Contributors
#
# This file is part of Mailboat.
#
# Mailboat is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Mailboat is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Mailboat.  If not, see <http://www.gnu.org/licenses/>.

from email.message import EmailMessage
from typing import Any, List, Optional

from aiosmtpd.smtp import AuthResult, LoginPassword, SMTP
from .mta import TransferAgent
from . import MailboatContext, StorageHub
from unqlite import UnQLite


class Mailboat(object):
    def __init__(
        self, *, hostname: str, mydomains: List[str], database_path: str, smtpd_port: Optional[int] = None
    ) -> None:
        if not smtpd_port:
            smtpd_port = 8025
        self.mydomains = mydomains
        self.hostname = hostname
        self.database_path = database_path
        self.database = UnQLite(database_path)
        self.storage_hub = StorageHub(self.database)
        self.transfer_agent = TransferAgent(
            mydomains=mydomains,
            local_delivery_handler=self.handle_local_delivering,
            database=self.storage_hub.database,
            smtpd_auth_handler=self.handle_smtpd_auth,
            hostname=self.hostname,
            self_name="transfer_agent.{}".format(self.hostname),
            smtpd_port=smtpd_port
        )
        super().__init__()
    
    async def handle_smtpd_auth(self, server: SMTP, method: str, data: Any) -> AuthResult:
        if method == 'login' or method == 'plain':
            assert isinstance(data, LoginPassword)
            username: bytes = data.login
            password: bytes = data.password
            username_s = username.decode('utf-8') # TODO (rubicon): support the other charsets
            result = await self.storage_hub.user_records.check_user_password(username_s, password)
            return AuthResult(success=result, handled=True)
        else:
            return AuthResult(success=False, handled=False)
    
    async def handle_local_delivering(self, message: EmailMessage):
        delivered_to = message['delivered-to']
