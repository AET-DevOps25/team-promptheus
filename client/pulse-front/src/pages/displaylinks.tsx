"use client"
import { useEffect, useState } from 'react'
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Copy } from 'lucide-react';

const formSchema = z.object({
  patstr: z.string().startsWith('ghp_', {
    message: "This is not a valid Github Token.",
  }),

  repolink: z.string().url({ message: "Invalid url" })

})



export type LinkListProps = {
  links: [string, string]; // Tuple of exactly 2 links
};



export function DisplayLinks( { links }: LinkListProps  ) {
  // ...


  const copytoclipboard = (text: string) => {


    // include pop up
    navigator.clipboard.writeText(text);

  }

  return (
      <div className="space-y-3 max-w-md mx-auto">

          <h3>These are the links you should share with the developers and managers respectively.</h3>

          {links.map((link, index) => 
          
          <div key={index} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 transition-colors">
            {link}
            
            <Button 
              onClick={() => copytoclipboard(link)} 
              variant="outline" 
              size="icon">
              <Copy />
            </Button>

          </div>
          
          )}


      </div>
  )
}
export default DisplayLinks