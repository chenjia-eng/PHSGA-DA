document.addEventListener("DOMContentLoaded", function () {
  // 获取DOM元素
  const aiIcon = document.getElementById("divai");
  const aiDialog = document.getElementById("ai-dialog");
  const aiClose = document.getElementById("ai-close");
  const aiMessages = document.getElementById("ai-messages");
  const aiInput = document.getElementById("ai-input");
  const aiSend = document.getElementById("ai-send");
  const aiHeader = document.getElementById("ai-header");

  // 基因相关关键词列表
  const geneKeywords = [
    "基因序列",
    "基因",
    "Gene",
    "DNA",
    "RNA",
    "基因组",
    "碱基",
    "测序",
    "转录",
    "翻译",
    "非编码RNA",
    "ncRNA",
    "转录组",
    "外显子",
    "内含子",
    "启动子",
    "ORF",
    "CDS",
    "UTR",
    "miRNA",
    "siRNA",
    "lncRNA",
    "circRNA",
    "甲基化",
    "突变",
    "SNP",
    "Indel",
    "变异",
    "表达量",
    "比对",
    "组装",
    "注释",
    "BLAST",
    "FASTA",
    "FASTQ",
    "NGS",
    "高通量测序",
  ];

  // 初始化对话框为隐藏状态
  aiDialog.style.display = "none";

  // 点击图标切换对话框显示状态
  let clickCount = 0;
  aiIcon.addEventListener("click", () => {
    clickCount++;
    if (clickCount % 2 === 1) {
      // 奇数次点击，显示对话框
      aiDialog.style.display = "flex";
      // 如果是第一次打开对话框，显示欢迎消息
      if (clickCount === 1) {
        addMessage(
          "bot",
          "Hello, I am an AI assistant focusing on gene sequence analysis. Do you have any questions about gene sequences, DNA, RNA, or related fields?"
        );
      }
    } else {
      // 偶数次点击，隐藏对话框
      aiDialog.style.display = "none";
    }
  });

  // 关闭对话框
  aiClose.addEventListener("click", () => {
    aiDialog.style.display = "none";
  });

  // 检查消息是否包含基因相关关键词
  function containsGeneKeyword(message) {
    return geneKeywords.some((keyword) =>
      message.toLowerCase().includes(keyword.toLowerCase())
    );
  }

  // 发送消息函数
  function sendMessage() {
    const message = aiInput.value.trim();
    if (message) {
      // 添加用户消息到对话框
      addMessage("user", message);
      aiInput.value = "";

      // 检查是否包含基因相关关键词
      if (!containsGeneKeyword(message)) {
        addMessage(
          "bot",
          "Sorry, please change to another question about gene sequences or related fields ~"
        );
        return;
      }

      // 调用后端API获取AI回复
      fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: message }),
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error("Network response was not ok");
          }
          return response.json();
        })
        .then((data) => {
          if (data && data.response) {
            addMessage("bot", data.response);
          } else {
            addMessage("bot", "抱歉，我无法理解服务器的回应。");
            console.error("Unexpected response format from server:", data);
          }
        })
        .catch((error) => {
          console.error("Error:", error);
          addMessage(
            "bot",
            "无法连接到AI服务，请检查后端是否运行。错误: " + error.message
          );
        });
    }
  }

  // 点击发送按钮或按Enter键发送消息
  aiSend.addEventListener("click", sendMessage);
  aiInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // 添加消息到对话框
  function addMessage(sender, text) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message");
    messageDiv.classList.add(
      sender === "user" ? "user-message" : "bot-message"
    );
    messageDiv.textContent = text;
    aiMessages.appendChild(messageDiv);
    aiMessages.scrollTop = aiMessages.scrollHeight;
  }

  // 使对话框可拖动
  let isDragging = false;
  let offsetX, offsetY;

  aiHeader.addEventListener("mousedown", (e) => {
    isDragging = true;
    offsetX = e.clientX - aiDialog.getBoundingClientRect().left;
    offsetY = e.clientY - aiDialog.getBoundingClientRect().top;
    aiDialog.style.cursor = "grabbing";
  });

  document.addEventListener("mousemove", (e) => {
    if (isDragging) {
      let newLeft = e.clientX - offsetX;
      let newTop = e.clientY - offsetY;

      const dialogWidth = aiDialog.offsetWidth;
      const dialogHeight = aiDialog.offsetHeight;
      const windowWidth = window.innerWidth;
      const windowHeight = window.innerHeight;

      newLeft = Math.max(0, Math.min(newLeft, windowWidth - dialogWidth));
      newTop = Math.max(0, Math.min(newTop, windowHeight - dialogHeight));

      aiDialog.style.left = newLeft + "px";
      aiDialog.style.top = newTop + "px";
    }
  });

  document.addEventListener("mouseup", () => {
    isDragging = false;
    aiDialog.style.cursor = "";
  });

  // 初始化对话框位置
  aiDialog.style.left = "calc(100% - 400px - 30px)";
  aiDialog.style.top = "80px";
});
