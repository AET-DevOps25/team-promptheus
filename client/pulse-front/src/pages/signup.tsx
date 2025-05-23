"use client"
import { useEffect, useState } from 'react'
import { zodResolver } from "@hookform/resolvers/zod"
import { useFieldArray, useForm } from "react-hook-form"
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
import DisplayLinks from './displaylinks'
import { LinkListProp } from "../components/LinkList";

const formSchema = z.object({
    patstr: z.string().startsWith('ghp_', {
      message: "This is not a valid Github Token.",
    }),
  
    repolink: z.string().url({ message: "Invalid url" })
  
  })


function SignupMain() {

    const [displayinglinks, setDisplayinglinks] = useState(false);
    const [linklist, setLinkList] = useState(["",""]); // TODO wiiiee??
    

    function ProfileForm() {
        // ...
    
        const [patsubmitted, setPatSubmitting] = useState(0)  
    
        const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            patstr: "",
        },
        })
    
    
    
        function onSubmit(values: z.infer<typeof formSchema>) {
        // Do something with the form values.
        // ✅ This will be type-safe and validated.
    
        setPatSubmitting(1)
        
        console.log("Submitting PAT")
        
        const pack = {
            pat : values.patstr,
            repolink: values.repolink
        };
    
    /*     const [linkdev, setLinkdev] = useState([]);
        const [linkman, setLinkman] = useState([]); */
    
    
    
            fetch('http://localhost:8090/api/providePAT' , 
            {
                method: "POST",
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(pack)
            }
            ).then(response => {
            if (!response.ok) {
                setPatSubmitting(0);
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
            }).then(data => {
            console.log(data);
            setPatSubmitting(0);
            setLinkList([data[0], data[1]]);
            setDisplayinglinks(true);
            });
    
        
        }
    
        
        return (
        <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
            
            
            <FormField
                control={form.control}
                name="patstr"
                render={({ field }) => (
                <FormItem>
                    <FormLabel>Personal Access Token</FormLabel>
                    <FormControl>
                    <Input type="password" placeholder="Your token here..." {...field} />
                    </FormControl>
                    <FormDescription>
                    Add a PAT with which the referenced repository can be accessed.
                    </FormDescription>
                    <FormMessage />
                </FormItem>
                )}
            />
    
            <FormField
                control={form.control}
                name="repolink"
                render={({ field }) => (
                <FormItem>
                    <FormLabel>Github Repository Link</FormLabel>
                    <FormControl>
                    <Input type="text" placeholder="Repository link here..." {...field} />
                    </FormControl>
                    <FormDescription>
                    The link to the repository accessible with the provided token.
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
  


    // main content
    return (
        <div>

            <div className="flex flex-col items-center justify-center min-h-svh">
            {displayinglinks ? <DisplayLinks links={ <LinkListProp links =  /> } /> : <ProfileForm></ProfileForm> }
            </div>
            
        </div>
    );

}




export default SignupMain

