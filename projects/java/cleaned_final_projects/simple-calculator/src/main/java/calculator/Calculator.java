package calculator;

public class Calculator {
    private final Arithmetics math = new Arithmetics();
    private final HistoryLogger logger = new HistoryLogger();

    public int performAdd(int x, int y) {
        if (Validator.isValid(x) && Validator.isValid(y)) {
            int result = math.add(x, y);
            logger.log("Add", result);
            return result;
        }
        return -1;
    }

    public int performSub(int x, int y) {
        if (Validator.isValid(x) && Validator.isValid(y)) {
            int result = math.sub(x, y);
            logger.log("Sub", result);
            return result;
        }
        return -1;
    }

    public int performMul(int x, int y) {
        if (Validator.isValid(x) && Validator.isValid(y)) {
            int result = math.mul(x, y);
            logger.log("Mul", result);
            return result;
        }
        return -1;
    }

    public int performDiv(int x, int y) {
        if (Validator.isValid(x) && Validator.isValid(y)) {
            int result = math.div(x, y);
            logger.log("Div", result);
            return result;
        }
        return -1;
    }

    public HistoryLogger getLogger() {
        return logger;
    }
}
