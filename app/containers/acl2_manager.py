class Acl2Manager:

    def check_formula(self, output) -> bool:
        correct: bool = False
        if ("Q.E.D." in output or ":REDUNDANT" in output) and "** FAILED **" not in output:
            correct = True
        return correct