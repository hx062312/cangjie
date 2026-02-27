package calculator;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class CalculatorTest {

    private Calculator calculator;

    @BeforeEach
    void setUp() {
        calculator = new Calculator();
        calculator.getLogger().clear();
    }

    @Test
    void testPerformAdd() {
        assertEquals(5, calculator.performAdd(2, 3));
        assertEquals(1, calculator.getLogger().getHistory().size());
    }

    @Test
    void testPerformSub() {
        assertEquals(1, calculator.performSub(3, 2));
        assertEquals(1, calculator.getLogger().getHistory().size());
    }

    @Test
    void testPerformMul() {
        assertEquals(6, calculator.performMul(2, 3));
        assertEquals(1, calculator.getLogger().getHistory().size());
    }

    @Test
    void testPerformDiv() {
        assertEquals(2, calculator.performDiv(6, 3));
        assertEquals(1, calculator.getLogger().getHistory().size());
    }

    @Test
    void testInvalidInput() {
        assertEquals(-1, calculator.performAdd(-1, 5));
        assertEquals(-1, calculator.performAdd(5, 1000));
        assertTrue(calculator.getLogger().getHistory().isEmpty());
    }

    @Test
    void testHistoryLogging() {
        calculator.performAdd(2, 3);
        calculator.performSub(5, 2);
        
        assertEquals(2, calculator.getLogger().getHistory().size());
        assertTrue(calculator.getLogger().getHistory().get(0).startsWith("Add:"));
        assertTrue(calculator.getLogger().getHistory().get(1).startsWith("Sub:"));
    }
}
