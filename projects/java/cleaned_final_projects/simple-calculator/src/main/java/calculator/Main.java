package calculator;

public class Main {
    public static void main(String[] args) {
        if (args.length == 0) {
            printUsage();
            return;
        }

        Calculator calc = new Calculator();
        String operation = args[0].toLowerCase();

        try {
            if (operation.equals("add") || operation.equals("+")) {
                if (args.length != 3) throw new IllegalArgumentException("add requires 2 numbers");
                int result = calc.performAdd(parseInt(args[1]), parseInt(args[2]));
                printResult(result);
            } else if (operation.equals("sub") || operation.equals("-")) {
                if (args.length != 3) throw new IllegalArgumentException("sub requires 2 numbers");
                int result = calc.performSub(parseInt(args[1]), parseInt(args[2]));
                printResult(result);
            } else if (operation.equals("mul") || operation.equals("*")) {
                if (args.length != 3) throw new IllegalArgumentException("mul requires 2 numbers");
                int result = calc.performMul(parseInt(args[1]), parseInt(args[2]));
                printResult(result);
            } else if (operation.equals("div") || operation.equals("/")) {
                if (args.length != 3) throw new IllegalArgumentException("div requires 2 numbers");
                int result = calc.performDiv(parseInt(args[1]), parseInt(args[2]));
                printResult(result);
            } else if (operation.equals("history") || operation.equals("h")) {
                for (String entry : calc.getLogger().getHistory()) {
                    System.out.println(entry);
                }
            } else if (operation.equals("help") || operation.equals("-h") || operation.equals("--help")) {
                printUsage();
            } else {
                System.err.println("Unknown operation: " + operation);
                printUsage();
            }
        } catch (NumberFormatException e) {
            System.err.println("Error: Please enter valid integers");
            System.exit(1);
        } catch (IllegalArgumentException e) {
            System.err.println("Error: " + e.getMessage());
            System.exit(1);
        }
    }

    private static int parseInt(String s) {
        return Integer.parseInt(s);
    }

    private static void printResult(int result) {
        if (result == -1) {
            System.err.println("Error: Invalid input. Values must be between 0 and 999");
            System.exit(1);
        }
        System.out.println(result);
    }

    private static void printUsage() {
        System.out.println("Simple Calculator - Command Line Tool");
        System.out.println("");
        System.out.println("Usage:");
        System.out.println("    calc <operation> <num1> <num2>");
        System.out.println("");
        System.out.println("Operations:");
        System.out.println("    add, +     Addition");
        System.out.println("    sub, -     Subtraction");
        System.out.println("    mul, *     Multiplication");
        System.out.println("    div, /     Division");
        System.out.println("");
        System.out.println("Examples:");
        System.out.println("    calc add 10 5");
        System.out.println("    calc + 10 5");
        System.out.println("    calc sub 20 8");
        System.out.println("    calc mul 6 7");
        System.out.println("    calc div 100 4");
        System.out.println("");
        System.out.println("Note: Input values must be between 0 and 999");
    }
}
