

def pretender_reversed(pretender_id):
    def reverse_url(inst, path):
        """
        Reverses the url using self.url and path given in parameter.

        Arguments:
        - `path`: the request path
        """

        server, port = inst.connection_handler.server, inst.connection_handler.port

        url = '%s/%s' % (pretender_id, inst.module)
        return url + path
    return reverse_url