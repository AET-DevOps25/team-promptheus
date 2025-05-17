"use client"
import { useState } from 'react'
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

const formSchema = z.object({
  username: z.string().startsWith('ghp_', {
    message: "This is not a valid Github Token.",
  }),
})




function ButtonMaker(){
  
 
  
}

export function ProfileForm() {
  // ...
  const [sendingtext, setsendingtext] = useState("S")
  const [patsubmitted, setPatSubmitting] = useState(0)  

  // 1. Define your form.
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      username: "",
    },
  })
 
  // 2. Define a submit handler.
  function onSubmit(values: z.infer<typeof formSchema>) {
    // Do something with the form values.
    // ✅ This will be type-safe and validated.

    setPatSubmitting(1)


    console.log(values)
  }

  


  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
        <FormField
          control={form.control}
          name="username"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Personal Access Token</FormLabel>
              <FormControl>
                <Input type="password" placeholder="Your token here..." {...field} />
              </FormControl>
              <FormDescription>
                Add a PAT with which the repository can be accessed.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
          {patsubmitted ? (
                <Button disabled>
                <Loader2 className="animate-spin" />
                Setting up. Please wait...
              </Button>
              ) :
              ( <Button type="submit">Start summarising</Button>)
            }
      </form>
    </Form>
  )
}
