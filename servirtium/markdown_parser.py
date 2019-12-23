#        Servirtium: Service Virtualized HTTP
#
#        Copyright (c) 2019, Paul Hammant and committers
#        All rights reserved.
#
#        Redistribution and use in source and binary forms, with or without
#        modification, are permitted provided that the following conditions are met:
#
#        1. Redistributions of source code must retain the above copyright notice, this
#        list of conditions and the following disclaimer.
#        2. Redistributions in binary form must reproduce the above copyright notice,
#        this list of conditions and the following disclaimer in the documentation
#        and/or other materials provided with the distribution.
#
#        THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#        ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#        WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#        DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
#        ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#        (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#        LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#        ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#        (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#        SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#        The views and conclusions contained in the software and documentation are those
#        of the authors and should not be interpreted as representing official policies,
#        either expressed or implied, of the Servirtium project.

import os

from servirtium.interactions import MockRecording, Interaction


class SimpleMarkdownParser:

    def __init__(self):
        self.markdown_files = []
        self.recordings = []

    def get_recording_from_method_name(self, method_name: str) -> MockRecording:
        recordings = list(filter(lambda mock: mock.file_name.replace('.md', '') in method_name, self.recordings))
        return recordings[0] if len(recordings) > 0 else None

    def is_valid_path(self, path: [MockRecording]) -> bool:
        return bool(filter(lambda x: x.path == path, [i.interactions for i in [m for m in self.recordings]]))

    def get_dict_from_headers_string(self, headers_string) -> {}:
        out = {}
        lines = headers_string.split('\n')

        for line in lines:
            line_split = [l.strip().replace('\n', '') for l in line.split(':')]
            out[line_split[0]] = line_split[1]
        return out

    def get_markdown_file_strings(self, mocks_path) -> [(str, str)]:
        file_strings = []

        for filename in os.listdir(mocks_path):
            file_path = os.path.join(mocks_path, filename)
            file_strings.append((filename, (self.get_file_content(file_path))))

        return file_strings

    def get_file_content(self, file_path):
        file = open(file_path, "r")
        content = file.read()
        return content

    def _set_mock_files(self, mock_files: [(str, str)]):
        for (name, content) in mock_files:
            self.markdown_files.append((name, content))
        self.recordings = [self.parse_markdown_string(n, c) for (n, c) in self.markdown_files]

    def parse_markdown_string(self, file_name, markdown_string) -> MockRecording:

        interaction_strings = ["## Interaction" + x for x in markdown_string.split("## Interaction") if len(x)]
        recording_interactions = list()

        for interaction in interaction_strings:
            raw_strings = interaction.split("##")
            clean_strings = []

            for string in raw_strings:
                if len(string):
                    clean_strings.append(string)

            interaction_description = clean_strings[0]
            interaction_split = interaction_description.split(' ')
            request_path = interaction_split[len(interaction_split) - 1].strip()

            assert clean_strings[1].startswith("# Request headers recorded for playback:"), \
                ("Servirtium request headers line missing from markdown")
            split = clean_strings[1].split('\n```\n')
            request_headers_string = split[1].strip()
            request_headers = self.get_dict_from_headers_string(request_headers_string)

            assert clean_strings[2].startswith("# Request body recorded for playback ("), \
                ("Servirtium request body line missing from markdown")
            request_body = clean_strings[2].split('\n```\n')[1].strip()

            assert clean_strings[3].startswith("# Response headers recorded for playback:"), \
                ("Servirtium response headers line missing from markdown")
            response_headers_string = clean_strings[3].split('\n```\n')[1].strip()
            response_headers = self.get_dict_from_headers_string(response_headers_string)

            assert clean_strings[4].startswith("# Response body recorded for playback ("), \
                ("Servirtium response body line missing from markdown")
            resp_body_chunk = clean_strings[4]
            response_code = resp_body_chunk.split('\n```\n')[0].split("(")[1].split(":")[0]
            response_body = resp_body_chunk.split('\n```\n')[1].strip()

            i = Interaction(request_path=request_path,
                            request_headers=request_headers, request_body=request_body,
                            response_headers=response_headers, response_body=response_body,
                            response_code=response_code)
            recording_interactions.append(i)

        return MockRecording(file_name=file_name, interactions=recording_interactions)
