"""
分词服务
提供中文分词功能（基于jieba）
"""

from typing import List, Dict, Set, Optional
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class TokenizerService:
    """分词服务"""
    
    # 默认停用词（中文常见停用词）
    DEFAULT_STOP_WORDS = {
        '的', '了', '是', '在', '有', '和', '就', '不', '人', '都', '一', '一个',
        '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看',
        '好', '自己', '这', '那', '里', '为', '而', '及', '与', '或', '等',
        '我', '你', '他', '她', '它', '我们', '你们', '他们',
        '这个', '那个', '这些', '那些', '这里', '那里',
        '什么', '怎么', '为什么', '哪里', '谁', '多少', '几',
        '吗', '呢', '吧', '啊', '呀', '哦'
    }
    
    def __init__(self, custom_stop_words: Optional[Set[str]] = None):
        """
        初始化分词服务
        
        Args:
            custom_stop_words: 自定义停用词集合
        """
        self.stop_words = self.DEFAULT_STOP_WORDS.copy()
        if custom_stop_words:
            self.stop_words.update(custom_stop_words)
        
        # 延迟加载jieba
        self._jieba = None
    
    @property
    def jieba(self):
        """延迟加载jieba"""
        if self._jieba is None:
            try:
                import jieba
                self._jieba = jieba
                logger.info("jieba分词库加载成功")
            except ImportError:
                logger.error("jieba未安装，请运行: pip install jieba")
                raise ImportError("jieba分词库未安装")
        return self._jieba
    
    def tokenize(
        self,
        text: str,
        mode: str = "default",
        use_stop_words: bool = True
    ) -> List[str]:
        """
        对文本进行分词
        
        Args:
            text: 输入文本
            mode: 分词模式 (default, search, all)
                - default: 精确模式
                - search: 搜索引擎模式
                - all: 全模式
            use_stop_words: 是否过滤停用词
            
        Returns:
            分词结果列表
        """
        if not text or not text.strip():
            return []
        
        # 根据模式分词
        if mode == "default":
            tokens = list(self.jieba.cut(text))
        elif mode == "search":
            tokens = list(self.jieba.cut_for_search(text))
        elif mode == "all":
            tokens = list(self.jieba.cut(text, cut_all=True))
        else:
            raise ValueError(f"不支持的分词模式: {mode}")
        
        # 过滤空白和单字符
        tokens = [t.strip() for t in tokens if t.strip() and len(t.strip()) > 1]
        
        # 过滤停用词
        if use_stop_words:
            tokens = [t for t in tokens if t not in self.stop_words]
        
        return tokens
    
    def batch_tokenize(
        self,
        texts: List[str],
        mode: str = "default",
        use_stop_words: bool = True
    ) -> List[List[str]]:
        """
        批量分词
        
        Args:
            texts: 文本列表
            mode: 分词模式
            use_stop_words: 是否过滤停用词
            
        Returns:
            分词结果列表
        """
        results = []
        for text in texts:
            tokens = self.tokenize(text, mode=mode, use_stop_words=use_stop_words)
            results.append(tokens)
        
        logger.info(f"批量分词完成: {len(texts)} 个文本")
        return results
    
    def extract_keywords(
        self,
        text: str,
        top_k: int = 20,
        with_weight: bool = False
    ) -> List[str] | List[tuple]:
        """
        提取关键词（基于TF-IDF）
        
        Args:
            text: 输入文本
            top_k: 提取的关键词数量
            with_weight: 是否返回权重
            
        Returns:
            关键词列表或(关键词, 权重)元组列表
        """
        try:
            import jieba.analyse
            
            if with_weight:
                keywords = jieba.analyse.extract_tags(
                    text,
                    topK=top_k,
                    withWeight=True
                )
            else:
                keywords = jieba.analyse.extract_tags(
                    text,
                    topK=top_k,
                    withWeight=False
                )
            
            return keywords
        except ImportError:
            logger.error("jieba.analyse模块不可用")
            return []
    
    def get_word_freq(
        self,
        texts: List[str],
        top_k: Optional[int] = None,
        use_stop_words: bool = True
    ) -> Dict[str, int]:
        """
        统计词频
        
        Args:
            texts: 文本列表
            top_k: 返回频率最高的K个词（None表示返回全部）
            use_stop_words: 是否过滤停用词
            
        Returns:
            词频字典 {词: 频率}
        """
        all_tokens = []
        for text in texts:
            tokens = self.tokenize(text, use_stop_words=use_stop_words)
            all_tokens.extend(tokens)
        
        # 统计词频
        word_freq = Counter(all_tokens)
        
        # 返回top_k
        if top_k:
            return dict(word_freq.most_common(top_k))
        else:
            return dict(word_freq)
    
    def add_stop_words(self, words: Set[str] | List[str]):
        """添加停用词"""
        if isinstance(words, list):
            words = set(words)
        self.stop_words.update(words)
        logger.info(f"添加 {len(words)} 个停用词")
    
    def remove_stop_words(self, words: Set[str] | List[str]):
        """移除停用词"""
        if isinstance(words, list):
            words = set(words)
        self.stop_words -= words
        logger.info(f"移除 {len(words)} 个停用词")
    
    def load_stop_words_file(self, file_path: str):
        """
        从文件加载停用词
        
        Args:
            file_path: 停用词文件路径（每行一个词）
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                words = {line.strip() for line in f if line.strip()}
            self.stop_words.update(words)
            logger.info(f"从文件加载 {len(words)} 个停用词")
        except Exception as e:
            logger.error(f"加载停用词文件失败: {e}")
    
    def add_user_dict(self, dict_path: str):
        """
        添加用户自定义词典
        
        Args:
            dict_path: 词典文件路径
        """
        try:
            self.jieba.load_userdict(dict_path)
            logger.info(f"加载用户词典: {dict_path}")
        except Exception as e:
            logger.error(f"加载用户词典失败: {e}")
    
    def suggest_new_words(
        self,
        text: str,
        score_threshold: float = 3.0
    ) -> List[tuple]:
        """
        发现新词（基于HMM）
        
        Args:
            text: 输入文本
            score_threshold: 分数阈值
            
        Returns:
            [(词, 分数), ...]
        """
        try:
            import jieba.analyse
            
            # 使用HMM模式分词，然后找高频但不在词典的词
            tokens = list(self.jieba.cut(text, HMM=True))
            word_freq = Counter(tokens)
            
            # 简单实现：返回高频词
            candidates = [
                (word, freq) for word, freq in word_freq.items()
                if freq >= score_threshold and len(word) >= 2
            ]
            
            return sorted(candidates, key=lambda x: x[1], reverse=True)
        except Exception as e:
            logger.error(f"新词发现失败: {e}")
            return []


# 全局单例
_tokenizer_instance = None


def get_tokenizer_service() -> TokenizerService:
    """获取分词服务单例"""
    global _tokenizer_instance
    if _tokenizer_instance is None:
        _tokenizer_instance = TokenizerService()
    return _tokenizer_instance

