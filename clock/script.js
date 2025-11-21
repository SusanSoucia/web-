// 绘制表盘刻度
function createTicks() {
    const ticksContainer = document.querySelector('.ticks');

for (let i = 0; i < 60; i++) {
    const tick = document.createElement('div');

    // 每 5 个刻度（对应整点）使用大刻度
    if (i % 5 === 0) {
        tick.classList.add('big');
    }

    tick.style.transform = `rotate(${i * 6}deg)`; 
    ticksContainer.appendChild(tick);
}
// 动态生成数字 1～12
const numbersContainer = document.querySelector('.numbers');
const radius = 120;  // 数字离中心的距离，可微调

for (let i = 1; i <= 12; i++) {
    const num = document.createElement('div');
    num.textContent = i;

    // 每个数字的角度（让 12 在正上方，所以 -90°）
    const angle = (i * 30 - 90) * Math.PI / 180;

    // 计算数字位置（圆周坐标）
    const x = 150 + radius * Math.cos(angle);
    const y = 150 + radius * Math.sin(angle);

    num.style.left = `${x}px`;
    num.style.top = `${y}px`;

    numbersContainer.appendChild(num);
}
}


function updateClock() {

    const now = new Date();
    const hours = now.getHours();
    const hourDig = hours.toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    const seconds = now.getSeconds().toString().padStart(2,'0');


    document.getElementById('hours').textContent = hourDig;


    document.getElementById('minutes').textContent = minutes;


    document.getElementById('seconds').textContent = seconds;


}

// 平滑指针
const secondHand = document.getElementById("second-hand");
const trailContainer = document.createElement("div"); // 尾迹容器
trailContainer.style.position = "absolute";
trailContainer.style.top = "0";
trailContainer.style.left = "0";
trailContainer.style.width = "100%";
trailContainer.style.height = "100%";
trailContainer.style.pointerEvents = "none";
document.querySelector(".clock").appendChild(trailContainer);

const trailLength = 10; // 尾迹点数
const trailPoints = [];

function updateClockSmooth() {
    const now = new Date();
    const ms = now.getMilliseconds();
    const seconds = now.getSeconds() + ms / 1000;
    const minutes = now.getMinutes() + seconds / 60;
    const hours = (now.getHours() % 12) + minutes / 60;

    const secondDeg = seconds * 6 - 90; // 秒针角度
    const minuteDeg = minutes * 6 - 90;
    const hourDeg = hours * 30 - 90;

    // 更新指针
    document.getElementById("second-hand").style.transform = `rotate(${secondDeg}deg)`;
    document.getElementById("minute-hand").style.transform = `rotate(${minuteDeg}deg)`;
    document.getElementById("hour-hand").style.transform = `rotate(${hourDeg}deg)`;

    // 更新尾迹
    trailPoints.push(secondDeg);
    if (trailPoints.length > trailLength) trailPoints.shift();

    trailContainer.innerHTML = ""; // 清空上一次尾迹
    trailPoints.forEach((deg, idx) => {
        const dot = document.createElement("div");
        dot.style.width = "4px";
        dot.style.height = "4px";
        dot.style.background = `rgba(255,0,0,${0.1 + 0.9 * idx / trailLength})`;
        dot.style.position = "absolute";
        dot.style.top = "50%";
        dot.style.left = "50%";
        dot.style.transformOrigin = "0% 50%";

        // 尾迹长度，越旧越短
        const trailRadius = 140 - 4 * (trailLength - idx);
        dot.style.transform = `rotate(${deg}deg) translateX(${trailRadius}px)`;
        dot.style.borderRadius = "50%";

        trailContainer.appendChild(dot);
    });

    requestAnimationFrame(updateClockSmooth);
}

createTicks();

setInterval(updateClock, 1000);


updateClockSmooth();

