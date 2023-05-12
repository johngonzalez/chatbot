'use client';

import { useState, useEffect, useRef } from 'react'

import Head from 'next/head'
import Header from '../components/Header'
import ChatMessages from '../components/ChatMessages'
import InputBar from '../components/InputBar'

export default function Home() {
    const [messages, setMessages] = useState([])
    const [input, setInput] = useState('')
    const [isFetching, setIsFetching] = useState(false);
    const inputRef = useRef(null)

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            handleSubmit(e)
        }
    }

    const handleSubmit = async (e) => {
        e.preventDefault()

        let updatedMessages = []
        if (input.trim()) {
            const userInputMessage = { text: input, sender: 'user' }
            if (messages.length === 0) {
                updatedMessages = [userInputMessage];
            } else {
                updatedMessages = [...messages, userInputMessage]
            }
            setMessages([...updatedMessages, { text: 'Consultando información...', sender: 'ia' }]);
            setIsFetching(true);
            await handleChat(updatedMessages)
            setInput('')
        }
    }

    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.style.height = 'auto'
            inputRef.current.style.height = inputRef.current.scrollHeight + 'px'
        }
    }, [input])

    const handleChat = async (updatedMessages) => {
        fetch('https://mxfrne-8000.csb.app/preguntas', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(updatedMessages),
        })
        .then(response => response.json())
        .then(({data}) => {
            setMessages(data)
            setIsFetching(false)
        })
    };

  
return (
    <>
        <Head>
            <title>Hable con Clara del Banco de Bogotá</title>
            <meta
                name="description"
                content="Hable con Clara del Banco de Bogotá."
            />
            <link rel="icon" href="/favicon.ico" />
            <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet" />
        </Head>
  
        <div className="h-screen flex flex-col bg-gray-800 text-gray-100 font-sans font-roboto">
            <Header />
            <div className="flex-1 overflow-auto p-4 flex justify-center">
                <ChatMessages messages={messages} isFetching={isFetching}/>
            </div>
            <div className="border-t border-gray-700">
                <InputBar
                    input={input}
                    setInput={setInput}
                    handleKeyDown={handleKeyDown}
                    handleSubmit={handleSubmit}
                />
            </div>
      </div>
    </>
  )
}