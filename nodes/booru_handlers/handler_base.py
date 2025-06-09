class BooruHandlerBase:
    def fetch(self, url, img_size, headers):
        raise NotImplementedError

    def parse(self, response, img_size):
        raise NotImplementedError
