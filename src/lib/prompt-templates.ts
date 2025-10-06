export const promtTemplateService = {
    generateRAGTemplate(query: string, match: string): string {
        const prompt = `According to this content: "${match}"
Answer this question: ${query}`;

        return prompt;
    }
};