#!/usr/bin/env python3
"""
Magic: The Gathering Comprehensive Rules Vector Database Builder

This script downloads the MTG Comprehensive Rules and converts it into a vector database
for semantic search and retrieval-augmented generation (RAG) applications.
"""

import requests
import re
import os
from typing import List, Dict, Tuple
import argparse
from dataclasses import dataclass
import json

# Vector database libraries
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import faiss
    import numpy as np
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


@dataclass
class RuleEntry:
    """Represents a single rule entry from the comprehensive rules."""
    rule_number: str
    title: str
    content: str
    section: str
    subsection: str = ""
    full_context: str = ""


class MTGRulesParser:
    """Parser for MTG Comprehensive Rules document."""
    
    def __init__(self, rules_text: str):
        self.rules_text = rules_text
        self.rules: List[RuleEntry] = []
        
    def parse(self) -> List[RuleEntry]:
        """Parse the rules text into structured rule entries."""
        lines = self.rules_text.split('\n')
        
        current_section = ""
        current_subsection = ""
        current_rule = None
        content_buffer = []
        
        # Regex patterns
        section_pattern = re.compile(r'^(\d+)\.\s+(.+)$')
        rule_pattern = re.compile(r'^(\d{3}\.\d+[a-z]*)\.\s*(.*)$')
        subsection_pattern = re.compile(r'^(\d{3})\.\s+(.+)$')
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and metadata
            if not line or line.startswith('Magic: The Gathering') or line.startswith('These rules are effective'):
                continue
                
            # Check for main sections (1. Game Concepts, 2. Parts of a Card, etc.)
            section_match = re.match(r'^(\d+)\.\s+(.+)$', line)
            if section_match and len(section_match.group(1)) == 1:
                # Save previous rule if exists
                if current_rule and content_buffer:
                    current_rule.content = ' '.join(content_buffer).strip()
                    current_rule.full_context = f"{current_section} - {current_rule.content}"
                    self.rules.append(current_rule)
                    
                current_section = f"{section_match.group(1)}. {section_match.group(2)}"
                current_rule = None
                content_buffer = []
                continue
                
            # Check for subsections (100. General, 101. The Magic Golden Rules, etc.)
            subsection_match = re.match(r'^(\d{3})\.\s+(.+)$', line)
            if subsection_match:
                # Save previous rule if exists
                if current_rule and content_buffer:
                    current_rule.content = ' '.join(content_buffer).strip()
                    current_rule.full_context = f"{current_section} - {current_subsection} - {current_rule.content}"
                    self.rules.append(current_rule)
                    
                current_subsection = f"{subsection_match.group(1)}. {subsection_match.group(2)}"
                current_rule = None
                content_buffer = []
                continue
                
            # Check for individual rules (100.1, 100.1a, etc.)
            rule_match = re.match(r'^(\d{3}\.\d+[a-z]*)\.\s*(.*)$', line)
            if rule_match:
                # Save previous rule if exists
                if current_rule and content_buffer:
                    current_rule.content = ' '.join(content_buffer).strip()
                    current_rule.full_context = f"{current_section} - {current_subsection} - {current_rule.content}"
                    self.rules.append(current_rule)
                    
                # Start new rule
                rule_num = rule_match.group(1)
                rule_content = rule_match.group(2)
                current_rule = RuleEntry(
                    rule_number=rule_num,
                    title="",
                    content="",
                    section=current_section,
                    subsection=current_subsection
                )
                content_buffer = [rule_content] if rule_content else []
                continue
                
            # Check for glossary terms or other special entries
            if line and current_rule is None and (current_section or current_subsection):
                # This might be a title or continuation
                if not content_buffer:  # Likely a title
                    current_rule = RuleEntry(
                        rule_number="",
                        title=line,
                        content="",
                        section=current_section,
                        subsection=current_subsection
                    )
                    content_buffer = []
                else:
                    content_buffer.append(line)
            elif line and current_rule:
                content_buffer.append(line)
                
        # Don't forget the last rule
        if current_rule and content_buffer:
            current_rule.content = ' '.join(content_buffer).strip()
            current_rule.full_context = f"{current_section} - {current_subsection} - {current_rule.content}"
            self.rules.append(current_rule)
            
        return self.rules


class VectorDatabaseBuilder:
    """Builds vector databases from parsed MTG rules."""
    
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        self.embedding_model_name = embedding_model
        self.model = None
        
    def initialize_model(self):
        """Initialize the embedding model."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("sentence-transformers is required. Install with: pip install sentence-transformers")
        
        print(f"Loading embedding model: {self.embedding_model_name}")
        self.model = SentenceTransformer(self.embedding_model_name)
        
    def build_chroma_db(self, rules: List[RuleEntry], db_path: str = "./mtg_rules_chroma"):
        """Build a ChromaDB vector database."""
        if not CHROMA_AVAILABLE:
            raise ImportError("chromadb is required. Install with: pip install chromadb")
            
        if not self.model:
            self.initialize_model()
            
        print("Building ChromaDB database...")
        
        # Initialize ChromaDB
        client = chromadb.PersistentClient(path=db_path)
        
        # Create or get collection
        collection = client.get_or_create_collection(
            name="mtg_rules",
            metadata={"description": "Magic: The Gathering Comprehensive Rules"}
        )
        
        # Prepare documents
        documents = []
        metadatas = []
        ids = []
        
        for i, rule in enumerate(rules):
            # Create searchable text
            if rule.rule_number:
                doc_text = f"Rule {rule.rule_number}: {rule.content}"
            else:
                doc_text = f"{rule.title}: {rule.content}" if rule.title else rule.content
                
            if not doc_text.strip():
                continue
                
            documents.append(doc_text)
            metadatas.append({
                "rule_number": rule.rule_number,
                "title": rule.title,
                "section": rule.section,
                "subsection": rule.subsection,
                "content": rule.content
            })
            ids.append(str(i))
            
        # Add to collection
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"Added {len(documents)} rules to ChromaDB at {db_path}")
        return client, collection
        
    def build_faiss_db(self, rules: List[RuleEntry], save_path: str = "./mtg_rules_faiss"):
        """Build a FAISS vector database."""
        if not FAISS_AVAILABLE:
            raise ImportError("faiss-cpu is required. Install with: pip install faiss-cpu")
            
        if not self.model:
            self.initialize_model()
            
        print("Building FAISS database...")
        
        # Prepare documents and embeddings
        documents = []
        metadata = []
        
        for rule in rules:
            if rule.rule_number:
                doc_text = f"Rule {rule.rule_number}: {rule.content}"
            else:
                doc_text = f"{rule.title}: {rule.content}" if rule.title else rule.content
                
            if not doc_text.strip():
                continue
                
            documents.append(doc_text)
            metadata.append({
                "rule_number": rule.rule_number,
                "title": rule.title,
                "section": rule.section,
                "subsection": rule.subsection,
                "content": rule.content,
                "full_text": doc_text
            })
            
        # Generate embeddings
        print("Generating embeddings...")
        embeddings = self.model.encode(documents)
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner product similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        index.add(embeddings.astype('float32'))
        
        # Save index and metadata
        os.makedirs(save_path, exist_ok=True)
        faiss.write_index(index, os.path.join(save_path, "mtg_rules.index"))
        
        with open(os.path.join(save_path, "metadata.json"), "w", encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        print(f"Saved FAISS index with {len(documents)} rules to {save_path}")
        return index, metadata


def download_rules(url: str = None) -> str:
    """Download the MTG Comprehensive Rules."""
    if url is None:
        url = "https://media.wizards.com/2025/downloads/MagicCompRules%2020250919.txt"
        
    print(f"Downloading rules from: {url}")
    response = requests.get(url)
    response.raise_for_status()
    return response.text


def search_chroma(client, collection, query: str, n_results: int = 5):
    """Search the ChromaDB collection."""
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    return results


def search_faiss(index, metadata, model, query: str, n_results: int = 5):
    """Search the FAISS index."""
    query_embedding = model.encode([query])
    faiss.normalize_L2(query_embedding)
    
    scores, indices = index.search(query_embedding.astype('float32'), n_results)
    
    results = []
    for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
        if idx != -1:  # Valid result
            results.append({
                'score': float(score),
                'metadata': metadata[idx]
            })
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Build MTG Comprehensive Rules Vector Database")
    parser.add_argument("--url", help="URL to download rules from")
    parser.add_argument("--input-file", help="Local rules file to use instead of downloading")
    parser.add_argument("--db-type", choices=["chroma", "faiss", "both"], default="both", 
                       help="Type of vector database to build")
    parser.add_argument("--output-dir", default="./mtg_db", help="Output directory for databases")
    parser.add_argument("--embedding-model", default="all-MiniLM-L6-v2", 
                       help="Sentence transformer model to use for embeddings")
    parser.add_argument("--test-query", help="Test query to run after building database")
    
    args = parser.parse_args()
    
    # Get rules text
    if args.input_file:
        print(f"Loading rules from file: {args.input_file}")
        with open(args.input_file, 'r', encoding='utf-8') as f:
            rules_text = f.read()
    else:
        rules_text = download_rules(args.url)
    
    # Parse rules
    print("Parsing rules...")
    parser = MTGRulesParser(rules_text)
    rules = parser.parse()
    print(f"Parsed {len(rules)} rule entries")
    
    # Build vector databases
    builder = VectorDatabaseBuilder(args.embedding_model)
    
    if args.db_type in ["chroma", "both"]:
        try:
            chroma_path = os.path.join(args.output_dir, "chroma")
            client, collection = builder.build_chroma_db(rules, chroma_path)
            
            # Test query
            if args.test_query:
                print(f"\nTesting ChromaDB with query: '{args.test_query}'")
                results = search_chroma(client, collection, args.test_query)
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i]
                    print(f"  {i+1}. Rule {metadata.get('rule_number', 'N/A')}: {doc[:100]}...")
                    
        except ImportError as e:
            print(f"Skipping ChromaDB: {e}")
    
    if args.db_type in ["faiss", "both"]:
        try:
            faiss_path = os.path.join(args.output_dir, "faiss")
            index, metadata = builder.build_faiss_db(rules, faiss_path)
            
            # Test query
            if args.test_query:
                print(f"\nTesting FAISS with query: '{args.test_query}'")
                results = search_faiss(index, metadata, builder.model, args.test_query)
                for i, result in enumerate(results):
                    meta = result['metadata']
                    print(f"  {i+1}. [Score: {result['score']:.3f}] Rule {meta.get('rule_number', 'N/A')}: {meta['full_text'][:100]}...")
                    
        except ImportError as e:
            print(f"Skipping FAISS: {e}")
    
    print("\nVector database build complete!")
    print(f"Databases saved to: {args.output_dir}")
    print("\nTo install required dependencies:")


if __name__ == "__main__":
    main()