package calculator;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class ArithmeticsTest {

    private final Arithmetics arithmetics = new Arithmetics();

    @Test
    void testAdd() {
        assertEquals(5, arithmetics.add(2, 3));
        assertEquals(0, arithmetics.add(-1, 1));
        assertEquals(100, arithmetics.add(50, 50));
    }

    @Test
    void testSub() {
        assertEquals(1, arithmetics.sub(3, 2));
        assertEquals(-2, arithmetics.sub(1, 3));
        assertEquals(0, arithmetics.sub(10, 10));
    }

    @Test
    void testMul() {
        assertEquals(6, arithmetics.mul(2, 3));
        assertEquals(0, arithmetics.mul(5, 0));
        assertEquals(-6, arithmetics.mul(-2, 3));
    }

    @Test
    void testDiv() {
        assertEquals(2, arithmetics.div(6, 3));
        assertEquals(0, arithmetics.div(5, 10));
        assertEquals(3, arithmetics.div(10, 3));
    }

    @Test
    void testDivByZero() {
        assertEquals(0, arithmetics.div(5, 0));
    }
}
