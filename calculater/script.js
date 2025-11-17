const calculator = document.querySelector('.calculator');
const keys = calculator.querySelector('.calculator-keys');
const display = document.getElementById('display');

// 存储计算状态的变量
let firstValue = null;
let operator = null;
let waitingForSecondValue = false; // 是否在等待用户输入第二个操作数

// ----------------------------------------------------
// 辅助函数
// ----------------------------------------------------

/**
 * 更新显示屏内容，并处理溢出问题。
 * @param {string | number} value 要显示的值。
 */
const updateDisplay = (value) => {
    const valueStr = String(value);
    // 限制显示位数，防止溢出
    if (valueStr.length > 15 && !valueStr.includes('e')) {
        // 使用科学计数法，保留8位小数
        display.value = parseFloat(value).toExponential(8); 
    } else {
        display.value = value;
    }
};

/**
 * 执行两个数之间的计算。
 * @param {string} n1 第一个操作数 (字符串)。
 * @param {string} op 运算符的动作名称 (e.g., 'add')。
 * @param {string} n2 第二个操作数 (字符串)。
 * @returns {number} 计算结果。
 */
const calculate = (n1, op, n2) => {
    const num1 = parseFloat(n1);
    const num2 = parseFloat(n2);

    if (op === 'add') return num1 + num2;
    if (op === 'subtract') return num1 - num2;
    if (op === 'multiply') return num1 * num2;
    if (op === 'divide') {
        if (num2 === 0) {
            return 'Error: Div by 0';
        }
        return num1 / num2;
    }
    return num2; 
};

/**
 * 处理所有的按钮动作逻辑（数字、运算符、功能键）。
 * @param {string} action 按钮的动作类型 (来自 data-action)。
 * @param {string} content 按钮的文本内容 (通常是数字)。
 */
const handleButtonAction = (action, content) => {
    const displayedNum = display.value;

    // 1. 数字键 (0-9)
    if (!isNaN(parseInt(content)) && content !== null) {
        if (displayedNum === '0' || waitingForSecondValue) {
            updateDisplay(content);
            waitingForSecondValue = false;
        } else {
            // 限制输入长度，防止过度溢出
            if (displayedNum.length < 15) {
                updateDisplay(displayedNum + content);
            }
        }
        return;
    }
    
    // 2. 小数点键 (.)
    if (action === 'decimal') {
        if (waitingForSecondValue) {
            updateDisplay('0.');
            waitingForSecondValue = false;
        } else if (!displayedNum.includes('.')) {
            updateDisplay(displayedNum + '.');
        }
        return;
    } 
    
    // 3. 运算符键 (+, -, ×, ÷)
    if (action === 'add' || action === 'subtract' || action === 'multiply' || action === 'divide') {
        if (firstValue && operator && !waitingForSecondValue) {
            // 链式计算：如果已经有值和运算符，先计算结果
            const result = calculate(firstValue, operator, displayedNum);
            updateDisplay(result);
            firstValue = result; // 结果作为新的第一个值
        } else {
            firstValue = displayedNum;
        }
        
        operator = action;
        waitingForSecondValue = true;
        return;
    } 
    
    // 4. 等号键 (=)
    if (action === 'calculate') {
        if (firstValue && operator) {
            const result = calculate(firstValue, operator, displayedNum);
            updateDisplay(result);

            // 重置状态
            firstValue = null;
            operator = null;
            waitingForSecondValue = false;
        }
        return;
    } 
    
    // 5. AC 键 (清零)
    if (action === 'clear') {
        updateDisplay('0');
        firstValue = null;
        operator = null;
        waitingForSecondValue = false;
        return;
    }
    
    // 6. 百分比 (%)
    if (action === 'percentage') {
        const value = parseFloat(displayedNum) / 100;
        updateDisplay(value);
        // 如果正在等待第二个值，需要将百分比应用于第一个操作数
        if (waitingForSecondValue) {
             firstValue = value;
        }
        return;
    }
    
    // 7. 正负号 (+/-)
    if (action === 'negate') {
        const value = parseFloat(displayedNum) * -1;
        updateDisplay(value);
        return;
    }
};

/**
 * 处理 Backspace 键的逻辑：删除显示屏上的最后一个字符。
 */
const handleBackspace = () => {
    let displayedNum = display.value;
    
    // 如果显示的是 '0' 或 'Error'，或者正在等待第二个操作数，则不进行操作
    if (displayedNum === '0' || displayedNum.startsWith('Error') || waitingForSecondValue) {
        return;
    }

    // 1. 删除最后一个字符
    displayedNum = displayedNum.slice(0, -1);

    // 2. 处理空字符串或只剩下负号的情况，确保显示 '0'
    if (displayedNum === '' || displayedNum === '-') {
        updateDisplay('0');
    } else {
        updateDisplay(displayedNum);
    }
};

// ----------------------------------------------------
// 事件监听器
// ----------------------------------------------------

// 1. 鼠标点击事件
keys.addEventListener('click', (e) => {
    if (!e.target.matches('button')) return;

    const key = e.target;
    const action = key.dataset.action;
    const keyContent = key.textContent;

    handleButtonAction(action, keyContent);
});

// 2. 键盘按下事件
document.addEventListener('keydown', (e) => {
    const key = e.key;
    let action = null;
    let content = null;

    // --- Backspace 处理 ---
    if (key === 'Backspace') {
        e.preventDefault(); 
        handleBackspace();

        // 视觉反馈：高亮AC键
        const targetButton = document.querySelector('button[data-action="clear"]');
        if (targetButton) {
            targetButton.classList.add('active-key');
            setTimeout(() => {
                targetButton.classList.remove('active-key');
            }, 100);
        }
        return; 
    }
    // ------------------------

    // 映射键盘按键到计算器动作
    if (key >= '0' && key <= '9') {
        content = key;
    } else if (key === '.') {
        action = 'decimal';
    } else if (key === '+') {
        action = 'add';
    } else if (key === '-') {
        action = 'subtract';
    } else if (key === '*' || key === 'x') {
        action = 'multiply';
    } else if (key === '/') {
        action = 'divide';
    } else if (key === 'Enter' || key === '=') {
        action = 'calculate';
    } else if (key === 'Escape' || key === 'c' || key === 'C') {
        action = 'clear';
    } else if (key === '%') {
        action = 'percentage';
    } 

    if (action || content) {
        e.preventDefault(); 
        handleButtonAction(action, content);
        
        // 可选：添加视觉反馈
        let targetButton;
        if (content) {
            targetButton = document.querySelector(`button[data-key="${content}"]`);
        } else if (action) {
            targetButton = document.querySelector(`button[data-action="${action}"]`);
        }

        if (targetButton) {
            targetButton.classList.add('active-key');
            setTimeout(() => {
                targetButton.classList.remove('active-key');
            }, 100);
        }
    }
});

// 初始化显示屏
updateDisplay('0');