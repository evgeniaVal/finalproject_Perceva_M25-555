class Currency:
    _name: str
    _code: str

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name: str):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Currency name cannot be empty.")
        self._name = name.strip()

    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, code: str):
        if (
            not isinstance(code, str)
            or not code.strip()
            or not 2 <= len(code.strip()) <= 5
            or not code.strip().isupper()
        ):
            raise ValueError("Currency code must be 2-5 uppercase letters.")
        self._code = code.strip().upper()

    def get_display_info(self) -> str:
        return f"{self._name} ({self._code})"
