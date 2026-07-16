class PropertyQueryBuilder:

    @staticmethod
    def build(filters: dict):

        query = {}

        if not filters:
            return query

        for k, v in filters.items():

            if isinstance(v, dict):
                query[k] = v

            elif isinstance(v, str):

                lv = v.strip().lower()

                if lv in ("true", "false"):
                    query[k] = lv == "true"

                else:
                    query[k] = {
                        "$regex": v,
                        "$options": "i",
                    }

            else:
                query[k] = v

        return query
