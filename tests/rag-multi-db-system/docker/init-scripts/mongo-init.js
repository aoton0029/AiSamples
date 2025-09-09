db = connect("mongodb://localhost:27017/rag_system");

db.documents.drop();
db.metadata.drop();

db.documents.insertMany([
    {
        document_id: "doc1",
        content: "This is the content of document 1.",
        metadata: {
            title: "Document 1",
            author: "Author A",
            created_at: new Date(),
            tags: ["tag1", "tag2"]
        }
    },
    {
        document_id: "doc2",
        content: "This is the content of document 2.",
        metadata: {
            title: "Document 2",
            author: "Author B",
            created_at: new Date(),
            tags: ["tag3", "tag4"]
        }
    }
]);

db.metadata.insertMany([
    {
        document_id: "doc1",
        description: "Metadata for document 1.",
        keywords: ["keyword1", "keyword2"]
    },
    {
        document_id: "doc2",
        description: "Metadata for document 2.",
        keywords: ["keyword3", "keyword4"]
    }
]);