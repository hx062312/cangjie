package calculator;

import java.util.ArrayList;
import java.util.List;

public class HistoryLogger {
    private final List<String> history = new ArrayList<>();

    public void log(String operation, int result) {
        String entry = operation + ": " + result;
        history.add(entry);
    }

    public List<String> getHistory() {
        return new ArrayList<>(history);
    }

    public void clear() {
        history.clear();
    }
}
