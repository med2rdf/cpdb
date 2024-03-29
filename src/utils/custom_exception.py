class JsonldConversionResultTypeException(Exception):
    """JSON-LD変換結果の型が期待と異なる場合の例外"""

    def __init__(
        self,
        message="JSON-LD conversion result was an unexpected type.",
    ):
        self.message = message
        super().__init__(self.message)
