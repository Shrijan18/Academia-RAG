<main className="main-content">
        <header className="top-header">
          <div className="header-left">
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="icon-btn"
            >
              <motion.div animate={{ rotate: isSidebarOpen ? 0 : 180 }}>
                <ChevronLeft size={20} />
              </motion.div>
            </button>
            <div className="header-title">Academic AI</div>
          </div>

          <div className="header-right">
            <div className="status-badge">
              <div className="status-dot" />
              Gemini 2.5
            </div>
            <button onClick={toggleTheme} className="icon-btn">
              {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
            </button>
          </div>
        </header>

        <div className="chat-container">
          <div className="chat-scroll-area" ref={scrollRef}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
              <AnimatePresence initial={false}>
                {messages.map((msg) => (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`message-wrapper ${msg.role}`}
                  >
                    <div className={`avatar ${msg.role}`}>
                      {msg.role === 'user' ? 'U' : 'T'}
                    </div>

                    <div className="message-content">
                      <div className="bubble">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            code: (props) => <CodeBlock {...props} theme={theme} />,
                            ul: ({ children }) => <ul className="markdown-list">{children}</ul>,
                            ol: ({ children }) => <ol className="markdown-list">{children}</ol>,
                            table: ({ children }) => (
                              <div className="table-wrapper">
                                <table className="markdown-table">{children}</table>
                              </div>
                            ),
                          }}
                        >
                          {msg.content}
                        </ReactMarkdown>
                      </div>

                      {/* Use optional chaining and ensure msg exists */}
                      {msg?.metadata?.source && (
                        <div className="metadata-container">
                          <div className="metadata">
                            <div className="doc-tag">
                              {/* Add optional chaining here too */}
                              {msg.metadata.source.toLowerCase().endsWith('.pdf') && <FileText size={12} />}
                              {/* ... other icons ... */}
                              <span>{msg.metadata.source}</span>
                            </div>

                            {/* Fix for score being undefined */}
                            {msg.metadata.score != null && (
                              <>
                                <span>•</span>
                                <span>Confidence {(msg.metadata.score * 100).toFixed(1)}%</span>
                              </>
                            )}
                          </div>

                          {/* Ensure source is used safely in the link */}
                          <div className="mt-4">
                            <a
                              href={`file:///${msg.metadata.source}`}
                              className="bg-[var(--accent)] p-2 rounded-lg text-sm flex items-center gap-2 transition-all hover:opacity-90 w-fit"
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              <Download size={14} />
                              Download Official {msg.metadata.source.split('\\').pop()}
                            </a>
                          </div>
                        </div>
                      )}
                    </div>
                  </motion.div>
                ))}
                {isLoading && (
                  <motion.div
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="message-wrapper bot"
                  >
                    <div className="avatar bot">T</div>
                    <div className="message-content">
                      <div className="bubble" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Loader2 size={18} className="animate-spin text-[var(--accent)]" />
                        <span>Analysing documents...</span>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>

          <div className="input-area">
            <div className="input-container">
              <button
                className="action-btn"
                title="Upload PDF, CSV or Audio"
                onClick={() => fileInputRef.current?.click()}
              >
                <Paperclip size={20} />
              </button>
              <input
                type="file"
                ref={fileInputRef}
                className="hidden"
                style={{ display: 'none' }}
                accept=".pdf,.csv,.wav,.mp3"
                onChange={handleFileUpload}
              />
              <textarea
                ref={textareaRef}
                value={input}
                onChange={handleInput}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Message Academia RAG..."
                className="textarea"
                rows={1}
                disabled={isLoading}
              />
              <button className="action-btn" title="Voice Input">
                <Mic size={20} />
              </button>
              <button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                className={`send-btn ${input.trim() && !isLoading ? 'active' : ''}`}
              >
                {isLoading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
              </button>
            </div>
            <p style={{ textAlign: 'center', fontSize: '11px', color: 'var(--text-tertiary)', marginTop: '12px' }}>
              FAISS-powered Multi-modal RAG. Verify sensitive enterprise data.
            </p>
          </div>
        </div>
      </main>